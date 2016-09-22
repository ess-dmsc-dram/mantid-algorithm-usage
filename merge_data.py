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
parser.add_argument('-c', '--max_count', metavar='N', type=int, default=-1, help='Include only algorithms used at most %(metavar)s times.')
parser.add_argument('-w', '--wide-output', action='store_true', help='Wide output, including module and path information.')
parser.add_argument('-b', '--include-blacklisted', action='store_true', help='Include algorithms from blacklist.')

args = parser.parse_args()


# http://stackoverflow.com/a/14981125
def eprint(*args, **kwargs):
    if config.verbose:
        print(*args, file=sys.stderr, **kwargs)


class AlgRecord:
    def __init__(self, data):
        self.ours = False
        self.has_test = False
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
            return 1
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


def get_line_count(record):
    source = record.path
    count = 0
    try:
        # Source lines
        count = count + get_file_length(source)
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
        if not record.is_test:
            if record.type == 'C++':
                testsource = re.sub('/src/' + basename + '.cpp', '/test/' + basename + 'Test.h', source)
                try:
                    count = count + get_file_length(testsource)
                    record.has_test = True
                except:
                    eprint('Failed to open test source ' + testsource)
                    pass
            elif record.type == 'Python':
                testsource = source.replace('/plugins/algorithms/', '/test/python/plugins/algorithms/').replace('.py', 'Test.py').replace('/WorkflowAlgorithms', '')
                try:
                    count = count + get_file_length(testsource)
                    record.has_test = True
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

    # Initialize superseeded field (replacement version found)
    for item in merged.values():
        alg_version = int(item.name[:-2:-1])
        superseeded = 'superseeded' if item.name[:-1] + str(alg_version+1) in merged else '          -'
        item.superseeded = superseeded

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


maxage = 24*60*60
update_cache(maxage)
merged = merge()

format_string = '{:9} {:5}% {:6} {:5} {:8} {:8} {:6} {:11} {:10} {:40}'
if args.wide_output:
    format_string = format_string + ' {} {}'

print('# ' + format_string.format('usecount', 'child', 'type', 'lines', 'codebase', 'testinfo', 'istest', 'versioninfo', 'deprecated', 'name', 'module', 'path'))

blacklist = load_blacklist()

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
    ours = 'ours' if r.ours else 'theirs'
    test = 'test' if r.is_test else '   -'
    tested = '       -' if r.has_test else 'untested'
    line_count = int(r.line_count) if r.line_count is not '-' else '    -'
    deprecated = 'deprecated' if r.is_deprecated else '         -'
    lines.append('  ' + format_string.format(
        count,
        int(100*r.get_internal_fraction()),
        r.type,
        line_count,
        ours,
        tested,
        test,
        r.superseeded,
        deprecated,
        r.name,
        r.module,
        r.path
        ))

for line in sorted(lines):
    print(line)
