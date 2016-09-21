import re
import parse_mantid_source
import parse_raw_results
import sys
import config

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


def get_line_count(record):
    source = record.path
    count = 0
    try:
        # Source lines
        with open(source, 'r') as myfile:
            count = count + len(myfile.read().split('\n'))
        basename = source.split('/')[-1].split('.')[0]
        # Header lines (if applicable)
        if (record.type == 'C++') and not record.is_test:
            module = record.module.split('/')[-1]
            header = re.sub('/src/' + basename + '.cpp', '/inc/Mantid' + module + '/' + basename + '.h', source)
            try:
                with open(header, 'r') as myfile:
                    count = count + len(myfile.read().split('\n'))
            except:
                eprint('Failed to open header ' + header)
                pass
        # Test lines (if applicable)
        if not record.is_test:
            if record.type == 'C++':
                testsource = re.sub('/src/' + basename + '.cpp', '/test/' + basename + 'Test.h', source)
                try:
                    with open(testsource, 'r') as myfile:
                        count = count + len(myfile.read().split('\n'))
                    record.has_test = True
                except:
                    eprint('Failed to open test source ' + testsource)
                    pass
            elif record.type == 'Python':
                testsource = source.replace('/plugins/algorithms/', '/test/python/plugins/algorithms/').replace('.py', 'Test.py').replace('/WorkflowAlgorithms', '')
                try:
                    with open(testsource, 'r') as myfile:
                        count = count + len(myfile.read().split('\n'))
                    record.has_test = True
                except:
                    eprint('Failed to open test source ' + testsource)
                    pass
        return str(count)
    except IOError:
        return '-'


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

    # Special cases
    # Q1D2:
    tmp = merged['Q1D.v2']
    tmp.name = 'Q1D2.v1'
    del merged['Q1D.v2']
    merged['Q1D2.v1'] = tmp

    return merged


merged = merge()

for r in merged.values():
    ours = 'ours' if r.ours else 'theirs'
    test = 'test' if r.is_test else '-'
    tested = '-' if r.has_test else 'untested'
    print('{:9} {:3}% {:6} {:4} {:6} {:8} {:4} {:11} {:40} {}'.format(
        r.get_count(),
        int(100*r.get_internal_fraction()),
        r.type,
        r.line_count,
        ours,
        tested,
        test,
        r.superseeded,
        r.name,
        r.module,
        r.path
        ))
