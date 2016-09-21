import parse_mantid_source
import parse_raw_results


class AlgRecord:
    def __init__(self, data):
        self.ours = False
        if isinstance(data, parse_mantid_source.AlgFileRecord):
            self.name = data.name
            self.path = data.path
            self.type = data.type
            self.is_test = data.is_test
            self.module = data.module
            self.ours = True
        elif isinstance(data, str):
            self.name = data
            self.path = ''
            self.type = ''
            self.is_test = False
            self.module = ''
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
    print('{:9} {:3}% {:6} {:6} {:4} {:11} {:40} {}'.format(r.get_count(), int(100*r.get_internal_fraction()), r.type, ours, test, r.superseeded, r.name, r.module, r.path))
