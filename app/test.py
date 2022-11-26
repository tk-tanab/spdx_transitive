# 2022-11-21T03:49:09Z
# YYYY-MM-DDThh:mm:ssZ
from datetime import datetime
import re

d = "cewmanyco :any"

print([i for i in re.split(" |\(|\)|\[.*?\]|:any", d) if i])

alist = [2,4,5,346,42,74,87,42]
len_alist = len(alist)

alist += [4325,6347,73473,65123,65236,26,2647,85,312]

new_alist = alist[len_alist:]
alist.append(33)
print(new_alist)
