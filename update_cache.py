#!/usr/bin/python3

import subprocess
import config
import time
import os
import stat
import download_results
import json
import parse_declared_algorithms
import sys

def file_age_in_seconds(pathname):
    try:
        return time.time() - os.stat(pathname)[stat.ST_MTIME]
    except OSError:
        return 100000000

def update_result_cache(maxage):
    filename = config.cache_dir + '/raw-results'
    if file_age_in_seconds(filename) > maxage:
        with open(filename, 'w') as myfile:
            myfile.write(json.dumps(download_results.get_data()))

def update_algorithm_cache(maxage):
    filename = config.cache_dir + '/declared-algorithms'
    if file_age_in_seconds(filename) > maxage:
        if sys.version_info >= (3,5):
            parse_declared_algorithms.update_cached_algorithm_information()
        else:
            subprocess.call(['./parse_declared_algorithms.sh', config.mantid_source, config.cache_dir])

def update_cache(maxage):
    update_result_cache(maxage)
    update_algorithm_cache(maxage)


if __name__ == '__main__':
    update_cache(0)
