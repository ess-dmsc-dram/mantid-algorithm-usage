Small tool for parsing and analysing algorithm usage statistics of Mantid.

The main script is `merge_data.py`.
It requires access to a Mantid source tree.
The path can be configured in `config.py`.
It defaults to `../mantid`.

Usage is:

```python
./merge_data.py # python3 merged_data.py
# Getting help
./merge_data.py -h
# Generate summary, listing algorithms up to use count 5, include only ours
./merge_data.py -s -c 5 -o
# Wide output including module names and filenames. Use less -S to
# avoid wrapping long lines, which creates unreadable output
./merge_data.py -o -c 20 -w | less -S
```
