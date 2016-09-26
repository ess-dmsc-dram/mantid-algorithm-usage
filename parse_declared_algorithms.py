import glob
import re
import config


def find_algorithms():
    print('Searching Mantid source tree for algorithms')
    exp = re.compile('(DECLARE_ALGORITHM|DECLARE_NEXUS_FILELOADER_ALGORITHM|DECLARE_FILELOADER_ALGORITHM|AlgorithmFactory.subscribe)\([A-Z]')
    exp_deprecated = re.compile('DeprecatedAlgorithm')
    declared = []
    deprecated = []
    for filetype in ['cpp', 'h', 'py']:
        for filename in glob.iglob(config.mantid_source + '/**/*.' + filetype, recursive=True):
            with open(filename, 'r') as myfile:
                lines = myfile.read().strip().split('\n')
                for line in lines:
                    if re.search(exp, line) is not None:
                        declared.append((filename, line))
                    if re.search(exp_deprecated, line) is not None:
                        if 'public' in line:
                            deprecated.append(filename)
    return declared, deprecated


def write_declared_algorithms(records):
    print('Writing declared-algorithms')
    with open(config.cache_dir + '/declared-algorithms', 'w') as myfile:
        for filename, line in records:
            myfile.write('{}:{}\n'.format(filename, line))


def write_deprecated_algorithms(records):
    print('Writing deprecated-algorithms')
    with open(config.cache_dir + '/deprecated-algorithms', 'w') as myfile:
        for line in records:
            myfile.write('{}\n'.format(line))


def update_cached_algorithm_information():
    declared, deprecated = find_algorithms()
    write_declared_algorithms(declared)
    write_deprecated_algorithms(deprecated)


if __name__ == '__main__':
    update_cached_algorithm_information()
