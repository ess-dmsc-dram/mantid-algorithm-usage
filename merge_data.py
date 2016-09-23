#!/usr/bin/python3

import argparse
import re
import parse_mantid_source
import parse_raw_results
import sys
import config
from update_cache import update_cache


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--ours', action='store_true', help='Include only algorithms defined in our codebase.')
parser.add_argument('-t', '--include-tests', action='store_true', help='Include algorithms that are defined in test files.')
parser.add_argument('-c', '--max-count', metavar='N', type=int, default=-1, help='Include only algorithms used at most %(metavar)s times.')
parser.add_argument('-w', '--wide-output', action='store_true', help='Wide output, including module and path information.')
parser.add_argument('-b', '--include-blacklisted', action='store_true', help='Include algorithms from blacklist.')
parser.add_argument('-s', '--summary', action='store_true', help='Output summary instead of table.')

args = parser.parse_args()


# http://stackoverflow.com/a/14981125
def eprint(*args, **kwargs):
    if config.verbose:
        print(*args, file=sys.stderr, **kwargs)


class AlgRecord:
    def __init__(self, data):
        self.ours = False
        self.has_test = False
        self.test_fraction = 0.0
        self.test_count = 0
        if isinstance(data, parse_mantid_source.AlgFileRecord):
            self.name = data.name
            self.path = data.path
            self.type = data.type
            self.is_test = data.is_test
            self.module = data.module
            self.ours = True
        elif isinstance(data, str):
            self.name = data
            self.path = '-'
            self.type = '-'
            self.is_test = False
            self.module = '-'
        else:
            raise RuntimeError('Bad init type ' + str(type(data)))
        self.count_direct = [0,0,0]
        self.count_internal = [0,0,0]

    def index_for_version(self, version):
        if version == '3.5':
            return 0
        if version == '3.6':
            return 1
        if version == '3.7':
            return 2
        raise RuntimeError('Unknown version ' + version)

    def add_result_data(self, result):
        index = self.index_for_version(result.version)
        count = result.count
        if result.is_child:
            self.count_internal[index] += count
        else:
            self.count_direct[index] += count

    def get_count(self):
        return sum(self.count_direct) + sum(self.count_internal)

    def get_internal_fraction(self):
        count = self.get_count()
        return 1.0 if count < 1 else float(sum(self.count_internal))/count


def get_file_length(filename):
    with open(filename, 'r') as myfile:
        return len(myfile.read().strip().split('\n'))


def get_test_count(filename):
    with open(filename, 'r') as myfile:
        text = myfile.read()
        return text.count('  void test') + text.count('  def test')


def get_line_count(record):
    source = record.path
    count = 0
    try:
        # Source lines
        source_lines = get_file_length(source)
        count = count + source_lines
        basename = source.split('/')[-1].split('.')[0]
        # Header lines (if applicable)
        if (record.type == 'C++') and not record.is_test:
            module = record.module.split('/')[-1]
            header = re.sub('/src/' + basename + '.cpp', '/inc/Mantid' + module + '/' + basename + '.h', source)
            try:
                count = count + get_file_length(header)
            except:
                eprint('Failed to open header ' + header)
                pass
        # Test lines (if applicable)
        test_lines = 0
        if not record.is_test:
            if record.type == 'C++':
                testsource = re.sub('/src/' + basename + '.cpp', '/test/' + basename + 'Test.h', source)
            elif record.type == 'Python':
                testsource = source.replace('/plugins/algorithms/', '/test/python/plugins/algorithms/').replace('.py', 'Test.py').replace('/WorkflowAlgorithms', '')
            try:
                test_lines = get_file_length(testsource)
                count = count + test_lines
                record.has_test = True
                record.test_fraction = float(test_lines)/source_lines
                record.test_count = get_test_count(testsource)
            except:
                eprint('Failed to open test source ' + testsource)
                pass
        return str(count)
    except IOError:
        return '-'


def is_deprecated(record, deprecated_headers):
    source = record.path
    if (record.type == 'C++') and not record.is_test:
        basename = source.split('/')[-1].split('.')[0]
        module = record.module.split('/')[-1]
        header = re.sub('/src/' + basename + '.cpp', '/inc/Mantid' + module + '/' + basename + '.h', source)
        return header in deprecated_headers
    return False


def merge():
    algs = parse_mantid_source.get_declared_algorithms()
    results = parse_raw_results.get_algorithm_results()

    merged = {}

    # Add known algorithms (found in Mantid source tree)
    for alg in algs:
        merged[alg.name] = AlgRecord(alg)

    # Add items from results, adding new records if unknown
    for result in results:
        merged.setdefault(result.name, AlgRecord(result.name)).add_result_data(result)

    # Initialize superseded field (replacement version found)
    for item in merged.values():
        alg_version = int(item.name[:-2:-1])
        superseded = 'superseded' if item.name[:-1] + str(alg_version+1) in merged else '          -'
        item.superseded = superseded

    # Add line counts
    for item in merged.values():
        item.line_count = get_line_count(item)

    # Add deprecation info
    with open(config.cache_dir + '/deprecated-algorithms', 'r') as myfile:
        deprecated_headers = myfile.read().split('\n')
        for item in merged.values():
            item.is_deprecated = is_deprecated(item, deprecated_headers)

    # Special cases
    # Q1D2:
    tmp = merged['Q1D.v2']
    tmp.name = 'Q1D2.v1'
    del merged['Q1D.v2']
    merged['Q1D2.v1'] = tmp

    return merged


def load_blacklist():
    with open('blacklist', 'r') as myfile:
        return myfile.read().strip().split('\n')


def get_format_string():
    format_string = '{:9} {:5}% {:6} {:5} {:7} {:6} {:8} {:8} {:6} {:11} {:10} {:40}'
    if args.wide_output:
        format_string = format_string + ' {} {}'
    return format_string


def print_header_line(format_string):
    print('# ' + format_string.format('usecount', 'child', 'type', 'lines', 'tst/src', 'tstcnt', 'codebase', 'testinfo', 'istest', 'versioninfo', 'deprecated', 'name', 'module', 'path'))

def format_algorithm_line(format_string, record):
    count = record.get_count()
    ours = 'ours' if record.ours else 'theirs'
    test = 'test' if record.is_test else '   -'
    tested = '       -' if record.has_test else 'untested'
    line_count = int(record.line_count) if record.line_count is not '-' else '    -'
    deprecated = 'deprecated' if record.is_deprecated else '         -'
    return '  ' + format_string.format(
        count,
        int(100*record.get_internal_fraction()),
        record.type,
        line_count,
        round(record.test_fraction, 2),
        record.test_count,
        ours,
        tested,
        test,
        record.superseded,
        deprecated,
        record.name,
        record.module,
        record.path
        )


def print_table(merged, blacklist):
    format_string = get_format_string()
    print_header_line(format_string)

    lines = []
    for r in merged.values():
        if args.ours and not r.ours:
            continue
        if (not args.include_tests) and (r.is_test):
            continue
        count = r.get_count()
        if args.max_count >= 0 and args.max_count < count:
            continue
        if (not args.include_blacklisted) and (r.name in blacklist):
            continue

        lines.append(format_algorithm_line(format_string, r))

    for line in sorted(lines):
        print(line)


class Summary():
    def __init__(self):
        self.total = 0
        self.unused = 0
        self.up_to_threshold = 0
        self.deprecated = 0
        self.superseded = 0
        self.untested = 0


def print_summary(merged, blacklist):
    line_count = 0
    line_count_unused = 0
    line_count_up_to_threshold = 0
    deprecated = []
    superseded = []
    format_string = get_format_string()
    unused = []
    below_max = []
    untested = []
    summary = Summary()
    for r in merged.values():
        if args.ours and not r.ours:
            continue
        if (not args.include_tests) and (r.is_test):
            continue
        if (not args.include_blacklisted) and (r.name in blacklist):
            continue

        count = r.get_count()
        try:
            this_count = int(r.line_count)
            line_count = line_count + this_count
            if count == 0:
                line_count_unused = line_count_unused + this_count
            if count <= args.max_count:
                line_count_up_to_threshold = line_count_up_to_threshold + this_count
        except ValueError:
            pass

        summary.total = summary.total + 1

        if r.is_deprecated:
            deprecated.append(format_algorithm_line(format_string, r))
            summary.deprecated = summary.deprecated + 1

        if not r.has_test:
            untested.append(format_algorithm_line(format_string, r))
            summary.untested = summary.untested + 1

        if r.superseded is 'superseded':
            superseded.append(format_algorithm_line(format_string, r))
            summary.superseded = summary.superseded + 1

        if count == 0:
            unused.append(format_algorithm_line(format_string, r))
            summary.unused = summary.unused + 1
            summary.up_to_threshold = summary.up_to_threshold + 1

        if 0 < count <= args.max_count:
            below_max.append(format_algorithm_line(format_string, r))
            summary.up_to_threshold = summary.up_to_threshold + 1

    print('=== Unused Algorithms ===')
    print_header_line(format_string)
    for line in sorted(unused):
        print(line)
    print('')

    print('=== Algorithms below threshold ===')
    print_header_line(format_string)
    for line in sorted(below_max):
        print(line)
    print('')

    print('=== Untested Algorithms ===')
    print_header_line(format_string)
    for line in sorted(untested):
        print(line)
    print('')

    print('=== Deprecated Algorithms ===')
    print_header_line(format_string)
    for line in sorted(deprecated):
        print(line)
    print('')

    print('=== Superseded Algorithms (newer version available) ===')
    print_header_line(format_string)
    for line in sorted(superseded):
        print(line)
    print('')

    print('=== Lines of code (algorithm source files, headers, and test sources) ===')
    print('{:7} lines for all algorithms'.format(line_count))
    if args.max_count > 0:
        print('{:7} lines for algorithms up to threshold use count {}'.format(line_count_up_to_threshold, args.max_count))
    print('{:7} lines for unused algorithms'.format(line_count_unused))
    print('')

    print('=== Summary ===')
    print('{:5} algorithms'.format(summary.total))
    if args.max_count > 0:
        print('{:5} algorithms up to threshold use count {}'.format(summary.up_to_threshold, args.max_count))
    print('{:5} unused algorithms'.format(summary.unused))
    print('{:5} deprecated algorithms'.format(summary.deprecated))
    print('{:5} superseded algorithms'.format(summary.superseded))
    print('{:5} untested algorithms'.format(summary.untested))
    print('')

    if args.ours:
        print('Output includes only results for algorithms in the Mantid codebase.')
    else:
        print('Output includes results for algorithms in the Mantid codebase AND from other sources.')



maxage = 24*60*60
update_cache(maxage)
merged = merge()
blacklist = load_blacklist()


if args.summary:
    print_summary(merged, blacklist)
else:
    print_table(merged, blacklist)
