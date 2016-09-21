from urllib.request import urlopen
import json

# Thanks to original author Matthew D. Jones
class AlgRecord:
    def __init__(self, name, count, is_child, version):
        self.name = name
        self.count = count
        self.is_child = is_child
        self.version = version

    def get_data_list(self):
        return [self.name, self.count, self.is_child, self.version]


def json_parser(data_string):
    data = json.loads(str(data_string))
    alg_records = []
    for record in data['results']:
        if record['type'] == 'Algorithm':
            alg_records.append(AlgRecord(record['name'], record['count'], record['internal'], record['mantidVersion']))
    return alg_records, data['next'] is not None


def get_data():
    table_data = []
    page_number = 1
    more = True
    while more:
        print("Collecting data from page " + str(page_number))
        resp = urlopen("http://reports.mantidproject.org/api/feature?page="+str(page_number)+"&format=json")
        alg_records, more = json_parser(resp.read().decode('utf-8'))
    
        for record in alg_records:
            table_data.append(record.get_data_list())
        page_number += 1

    return table_data
