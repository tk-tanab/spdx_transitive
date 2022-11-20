import deb_spdx
import re
import subprocess
import os
import sys


def make_pv_vrp_dict(pv_dict: dict[str, str], vrp_dict: dict[str, list[list[str]]]):
    """
    pv_dict と vrp_dict の作成
    
    Args: 
        pv_dict: パッケージとバージョンの対応辞書
        vrp_dict: Virtual と Replace の辞書
    """
    dpkg_status_list = subprocess.run(
        ["dpkg-query", "-W", "-f=${binary:Package}\t${Provides}\t${Replaces}\t${Version}\n"], capture_output=True, text=True
    ).stdout.splitlines()

    # Virtual と Replace の辞書作成
    for dpkg_s in dpkg_status_list:

        # dpkg_s_list: Package, Provides, Replaces, Version
        dpkg_s_list = re.sub(":.*?\t", "\t", dpkg_s.strip()).split('\t')

        pv_dict[dpkg_s_list[0]] = dpkg_s_list[3]

        if dpkg_s_list[1]:
            add_vrp_dict(dpkg_s_list[1], dpkg_s_list[0], vrp_dict)
        if dpkg_s_list[2]:
            add_vrp_dict(dpkg_s_list[2], dpkg_s_list[0], vrp_dict)

    # 重複削除
    for key, value in vrp_dict.items():
        vrp_dict[key] = list(map(list, set(map(tuple, value))))

def add_vrp_dict(vrp_names: str, p_name: str, vrp_dict: dict[str, list[list[str]]]):
    """
    Virtual と Replace の辞書に情報を追加
    
    Args: 
        vrp_names: 代替できるパッケージの名前の列記
        p_name: リアルなパッケージの名前
        vrp_dict: Virtual と Replace の辞書
    """
    vrp_name_list = vrp_names.split(', ')
    for vrp_name in vrp_name_list:
        vrp_name_split = [i for i in re.split(" |\(|\)|\[.*?\]", vrp_name) if i]
        # vrp_name_split: Virtual or Replace Package, (比較演算子, Version)

        if vrp_name_split[0] in vrp_dict:
            vrp_dict[vrp_name_split[0]].append([p_name] + vrp_name_split[1:])
        else:
            vrp_dict[vrp_name_split[0]] = ([[p_name] + vrp_name_split[1:]])

if __name__ == "__main__":
    package_name = "xxd"
    auth_name = "Taketo"

    pv_dict: dict[str, str] = {} # {p_name: version}
    vrp_dict: dict[str, list[list[str]]] = {} # {vrp_name: [[p_name, c_operator, version]]}

    make_pv_vrp_dict(pv_dict, vrp_dict)

    # ディレクトリ記憶
    cwd = os.getcwd()

    # すでに同名のSPDX展開ディレクトリがある場合はエラー出力
    # 完全に同名の複数バージョンはない
    dir_name = os.path.dirname(__file__) + "/../SPDX/" + package_name
    try:
        os.makedirs(dir_name)
        os.chdir(dir_name)
    except FileExistsError:
        print("That SPDX already exists")
        sys.exit()

    # 実行
    deb_class = deb_spdx.Deb_Spdx()
    deb_class.run(package_name, auth_name, [])

    os.chdir(cwd)

    # パッケージの種類判定 todo
    # debianの事前処理

