import argparse
import json
from copy import deepcopy

modes = [ "summary", "table", "unified", "default" ]
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-m', '--mode', choices=modes, default='table', help='Specify output mode.')
#parser.add_argument('-t', '--table', action='store_true',
#                    help='Prints a table of results.')
#parser.add_argument('-u', '--unified-counts', action='store_true',
#                    help='Prints unified usage counts (sum of direct and internal calls).')
#parser.add_argument('-c', '--controllee', type=str, default='BraggPeakEventGenerator', help='Specify controllee.')
#parser.add_argument('-H', '--host', type=str, default='localhost', help='Host to connect to.')
#parser.add_argument('-p', '--port', type=str, default='10002', help='Port to connect to.')

args = parser.parse_args()



#for i in $(seq 0 35); do wget http://reports.mantidproject.org/api/feature?page=$i; done

#for i in range(1, 33):
def loadResults():
    results = []
    for i in range(1, 33):
        with open('feature?page=' + str(i), 'r') as myfile:
            data=myfile.read().replace('\n', '')
            results = results + json.loads(data)['results']
    # Remove entries that are probably not algorithms, i.e., those without version suffix
    return [ x for x in results if x['name'][:-1].endswith('.v') ]

def loadUnusedAlgorithms():
    with open('unused-algorithms', 'r') as myfile:
        return myfile.read().strip().split('\n')

def loadAllAlgorithms():
    with open('all-algorithms', 'r') as myfile:
        return myfile.read().strip().split('\n')

def extractAlgorithms(results):
    return list(set([ item['name'] for item in results ]))

def unusedAlgorithmsSanityCheck(unused, used):
    for alg in unused:
        if alg in used:
            raise RuntimeError("Algorithm listed in both used and unused.")

def makeAlgorithmList(results):
    unusedAlgs = loadUnusedAlgorithms()
    usedAlgs = extractAlgorithms(results)
    unusedAlgorithmsSanityCheck(unusedAlgs, usedAlgs)
    return sorted(unusedAlgs + usedAlgs)

def makeTable():
    results = loadResults()
    algorithms = makeAlgorithmList(results)
    mantidAlgs = loadAllAlgorithms()
    emptyDict = {
            '3.5':{'internal':0, 'direct':0},
            '3.6':{'internal':0, 'direct':0},
            '3.7':{'internal':0, 'direct':0},
            'ours':False
            }
    table = {}
    for alg in algorithms:
        table[alg] = deepcopy(emptyDict)
    for result in results:
        name = str(result['name'])
        version = str(result['mantidVersion'])
        mode = 'internal' if result['internal'] else 'direct'
        count = result['count']
        table[name][version][mode] = count
    for name, data in table.iteritems():
        if name in mantidAlgs:
            data['ours'] = True
    return table


results = loadResults()
algorithms = makeAlgorithmList(results)


table = makeTable()


def filterByVersion(results, version):
    return [ result for result in results if result['mantidVersion'] == str(version) ]

def unifyCounts(results):
    unified = {}
    for result in results:
        name = result['name']
        if name in unified:
            unified[name] += result['count']
        else:
            unified[name] = result['count']
    tmp = []
    for key,value in unified.iteritems():
        tmp.append({'count':value, 'name':key})
    return tmp

results35 = filterByVersion(results, 3.5)
results36 = filterByVersion(results, 3.6)
results37 = filterByVersion(results, 3.7)


#print('{} items loaded'.format(len(results)))
#print('{} items have version 3.5'.format(len(results35)))
#print('{} items have version 3.6'.format(len(results36)))
#print('{} items have version 3.7'.format(len(results37)))
#print('')

if args.mode == "table":
    for name, data in table.iteritems():
        direct35 = data['3.5']['direct']
        direct36 = data['3.6']['direct']
        direct37 = data['3.7']['direct']
        internal35 = data['3.5']['internal']
        internal36 = data['3.6']['internal']
        internal37 = data['3.7']['internal']
        count35 = internal35 + direct35
        count36 = internal36 + direct36
        count37 = internal37 + direct37
        count = count35+count36+count37
        internal = internal35+internal36+internal37
        internal_fraction = 1.0 if count < 1 else float(internal)/count
        alg_version = int(name[:-2:-1])
        superseeded = 'superseeded' if name[:-1] + str(alg_version+1) in table else '          -'
        ours = '  ours' if data['ours'] else 'theirs'
        print('{:9} {:9} {:9} {:3}% {} {} {}'.format(count35, count36, count37, int(100*internal_fraction), superseeded, ours, name))
        #print('{:9} ({:3.1f}) {:9} ({:3.1f}) {:9} ({:3.1f}) {}'.format(count35, internal35/count35, count36, internal36/count36, count37, internal37/count37, name))
elif args.mode == "summary":
    print("{} algorithms (any version)".format(len(table)))
    unused = 0
    unused37 = 0
    below5 = 0
    for name, data in table.iteritems():
        direct35 = data['3.5']['direct']
        direct36 = data['3.6']['direct']
        direct37 = data['3.7']['direct']
        internal35 = data['3.5']['internal']
        internal36 = data['3.6']['internal']
        internal37 = data['3.7']['internal']
        count35 = internal35 + direct35
        count36 = internal36 + direct36
        count37 = internal37 + direct37
        if count35 + count36 + count37 == 0:
            unused = unused + 1
        if count37 == 0:
            unused37 = unused37 + 1
        if count35 + count36 + count37 < 5:
            below5 = below5 + 1
    print("{} unused".format(unused))
    print("{} used less than 5 times".format(below5))
    print("{} unused in 3.7".format(unused37))
elif args.mode == "unified":
    unified = unifyCounts(results37)
    sorted_results = sorted(unified, key=lambda k : k['count'], reverse=True)
    for item in sorted_results:
        print('{:9} {}'.format(item['count'], item['name']))
else:
    sorted_results = sorted(results, key=lambda k : k['count'], reverse=True)

    for item in sorted_results:
        print('{:9} {:8} {} {}'.format(item['count'], 'internal' if item['internal'] else 'direct', item['mantidVersion'], item['name']))
