import pandas as pd
import matplotlib.pyplot as plt

# Data gathered by running the following in Framework/ (this takes about 1 hour, so the logs are also added to git for convenience):
# for file in $(grep -rl AlgorithmFactory.subscribe\(); do git blame -M -C20 -w $file | grep AlgorithmFactory.subscribe\(; done | tee log-py
# for file in $(grep -rl DECLARE_ALGORITHM); do git blame -M -C20 -w $file | grep DECLARE_ALGORITHM; done | tee mantid-algorithm-usage/log-cpp

filename='log-cpp'

dates = []
names = []
with open(filename) as f:
    lines = [line.rstrip('\n') for line in f]
    for line in lines:
        if '#define' in line:
            continue
        if '// DECLARE_ALGORITHM' in line:
            continue
        fields = line.split()
        for i,field in enumerate(fields):
            if field.startswith('DECLARE_ALGORITHM('):
                dates.append(fields[i-4])
                names.append(field[18:-1])

df = pd.DataFrame(data={"date":dates, "name":names})
df["date"] = df["date"].astype("datetime64[ns]")

cpp_algs = df.groupby([df["date"].dt.year, df["date"].dt.quarter])["date"].count()

filename='log-py'

dates = []
names = []
with open(filename) as f:
    lines = [line.rstrip('\n') for line in f]
    for line in lines:
        fields = line.split()
        for i,field in enumerate(fields):
            if field.startswith('AlgorithmFactory.subscribe('):
                dates.append(fields[i-4])
                names.append(field[27:-1])

df = pd.DataFrame(data={"date":dates, "name":names})
df["date"] = df["date"].astype("datetime64[ns]")

py_algs = df.groupby([df["date"].dt.year, df["date"].dt.quarter])["date"].count()

combined = pd.DataFrame({'C++':cpp_algs, 'Python':py_algs})
combined.index.names=['year','quarter']
combined.cumsum().plot(kind="bar", stacked=True, figsize=(14,9))
plt.title("Cumulative number of algorithms")
plt.savefig("cumulative-algorithm-count.png", dpi=200)
