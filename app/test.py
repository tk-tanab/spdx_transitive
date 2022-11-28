# 2022-11-21T03:49:09Z
# YYYY-MM-DDThh:mm:ssZ
from datetime import datetime
import os

def get_dir_size(path='.'):
    total = 0
    counter = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
                counter += 1
        else:
            print("file_num", counter)
    return total

print(get_dir_size('SPDX/perl'))
# print(os.getcwd())