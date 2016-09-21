# mantid-algorithm-usage
Small tool for parsing and analysing algorithm usage statistics of Mantid

The main script is `merge_data.py`. Usage is:

```python
./merge_data.py # python3 merged_data.py
# Getting help
./merge_data.py -h
# Use less -S to avoid wrapping long lines, which creates unreadable output
./merge_data.py -o -c 20 | less -S
```
