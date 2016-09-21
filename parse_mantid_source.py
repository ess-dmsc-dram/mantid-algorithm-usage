import re
import config


def load_declared_algorithms():
    with open(config.cache_dir + '/declared-algorithms', 'r') as myfile:
        return myfile.read().strip().replace('()', '').split('\n')


class AlgFileRecord:
    def __init__(self, data):
        split = data.split(':')
        n = re.search(r"\((\w+)\)", split[1])
        self.path = split[0]
        name = n.group(1)
        if self.path.endswith('.cpp') or self.path.endswith('.h'):
            self.type = 'C++'
        elif self.path.endswith('.py'):
            self.type = 'Python'
        else:
            self.type = 'unknown'
        self.is_test = '/test/' in self.path
        if self.type == 'C++':
            if self.is_test:
                module = re.findall(config.mantid_source + '/(.*?)/test/*', self.path)
            else:
                module = re.findall(config.mantid_source + '/(.*?)/src/*', self.path)
        else:
            if self.is_test:
                module = re.findall(config.mantid_source + '/(.*?)/test/*', self.path)
            else:
                module = re.findall(config.mantid_source + '/(.*?)/plugins/*', self.path)
        if not module:
            module = re.findall(config.mantid_source + '/(.*?)/' + name + '*', self.path)
        if module:
            self.module = module[0]
        else:
            self.module = None
        self.name = self._get_name_with_version(name)

    def _get_name_with_version(self, name):
        try:
            version = int(name[-1])
            name = name[:-1]
        except ValueError:
            version = 1
        return name + '.v' + str(version)


def get_declared_algorithms():
    lines = load_declared_algorithms()
    records = []
    for line in lines:
        records.append(AlgFileRecord(line))
    return records


if __name__ == '__main__':
    for record in get_declared_algorithms():
        print('{} {} {} {} {}'.format(record.name, record.path, record.type, record.is_test, record.module))
