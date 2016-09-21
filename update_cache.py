import subprocess
import config

subprocess.call(['./parse_declared_algorithms.sh', config.mantid_source, './cache'])
