import re
import os
import subprocess

# print(re.split(",| |[|]|\(.*?\)|\[.*?\]", "[frewc|f]c ew(cferw)f"))

# tv_dict = {
#     "Package": [
#         {
#             "PackageName": "wawawawa"
#         }
#     ]
# }

# if "rioi" in tv_dict:
#     package_dict = tv_dict["rioi"]
# print(package_dict)

def compare_version(v1, v2, c_operator)-> bool:
    try:
        subprocess.run(
            ["dpkg", "--compare-versions", v1, c_operator, v2], check=True
        )
    except subprocess.CalledProcessError as e:
        return False
    return True

def add_external_ref(p_name):
    with open(p_name + ".spdx", mode="r", encoding="utf-8") as f:
        lines_strip = [s.strip() for s in f.readlines()]
    for line in lines_strip:
        if "DocumentNamespace" in line:
            ref_space = line[19:]
            break
    else:
        return
    print(ref_space)

v1 = "1.28-1ubuntu1"
v2 = "1.25.3-1.1ubuntu2~"
co = "lt"
p_name = "/home/tk-tanab/taketo/syuron/git/spdx_transitive/SPDX/xxd/xxd"

add_external_ref(p_name)

