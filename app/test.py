from unicodedata import name
import deb
from pprint import pprint
import shutil
import subprocess
import os
import control_to_dict
import tv_to_dict
import merge_tv_control
import json
import re

pprint(re.split(",| |[|]|\(.*?\)|\[.*?\]", "[frewc|f]c ew(cferw)f"))

dpkg_status_list = subprocess.run(
    ["dpkg-query", "-W", "-f=${binary:Package}\t${Provides}\t${Replaces}\t${Version}\n"], capture_output=True, text=True
).stdout.splitlines()

# print(dpkg_status_list)

def add_vrp_dict(vrp_names, p_name, vrp_dict):
    """
    Virtual と Replace の辞書に情報を追加
    vrp_dict = {
        vrp_name: [[p_name, c_operator, version]]
    }
    """
    vrp_name_list = vrp_names.split(', ')
    for vrp_name in vrp_name_list:
        vrp_name_split = [i for i in re.split(" |\(|\)|\[.*?\]", vrp_name) if i]
        # vrp_name_split: Virtual or Replace Package, (比較演算子, Version)

        if vrp_name_split[0] in vrp_dict:
            vrp_dict[vrp_name_split[0]].append([p_name] + vrp_name_split[1:])
        else:
            vrp_dict[vrp_name_split[0]] = ([[p_name] + vrp_name_split[1:]])

# Virtual と Replace の辞書作成
pv_dict = {}
vrp_dict = {}
for dpkg_s in dpkg_status_list:

    # dpkg_s_list: Package, Provides, Replaces, Version
    dpkg_s_list = re.sub(":.*?\t", "\t", dpkg_s.strip()).split('\t')

    # pv_dict = {p_name: version}
    pv_dict[dpkg_s_list[0]] = dpkg_s_list[3]

    if dpkg_s_list[1]:
        add_vrp_dict(dpkg_s_list[1], dpkg_s_list[0], vrp_dict)
    if dpkg_s_list[2]:
        add_vrp_dict(dpkg_s_list[2], dpkg_s_list[0], vrp_dict)

# 重複削除
for key, value in vrp_dict.items():
    vrp_dict[key] = list(map(list, set(map(tuple, value))))

pprint(pv_dict)
pprint(vrp_dict)


# ディレクトリ作成
cwd = os.getcwd()
# ワーキングディレクトリに移動
os.chdir(os.path.dirname(__file__) + "/work")
# すでに同名のSPDXディレクトリがある場合はエラー出力
# 完全に同名の複数バージョンはない
dir_name = "SPDX/" + package_name
try:
    os.makedirs(dir_name)
    os.chdir(dir_name)
except FileExistsError:
    print("That SPDX already exists")

# 実行 Todo


os.chdir(cwd)