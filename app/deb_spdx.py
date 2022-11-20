from pprint import pprint
import shutil
import subprocess
import os
import control_to_dict
import tv_to_dict
import json
import hashlib
import uuid
import dict_to_tv

class Deb_Spdx:

    pv_dict: dict[str, str] # {p_name: version}
    vrp_dict: dict[str, list[list[str]]] # {vrp_name: [[p_name, c_operator, version]]}
    tv_dict: dict[str, list[dict[str, list[str]]]] # SPDX.json 参照
    control_dict: dict[str, list[str]] # {field_name: [values]}

    def print_var(self):
        print(self.tv_dict)

    def compare_version(self, restrict_v_list, v_list):
        # dpkg --compare-versions 1.28-1ubuntu1 gt 1.25.3-1.1ubuntu2~ && echo true

        print(3)

    def rm_license_dup(self, lic_dict_list):
        # ライセンスの重複削除
        lic_rm_dup_list = []
        for lic_dict in lic_dict_list:
            for lic_rm_dup in lic_rm_dup_list:
                if lic_rm_dup == lic_dict:
                    break
            else:
                lic_rm_dup_list.append(lic_dict)
        else:
            return lic_rm_dup_list

    def merge_tv_control(self, auth_name: str):
        """
        spdxファイルにcontrolファイルの情報を結合
        パッケージ間の依存関係情報 以外を追加・修正

        Args: 
            auth_name(str): 作者名
        """
        tv_dict = self.tv_dict
        control_dict = self.control_dict

        # パッケージ情報の追加・修正
        package_dict = tv_dict["Package"][0]
        package_dict["PackageName"] = control_dict["Package"]
        package_dict["PackageVersion"] = control_dict["Version"]
        package_dict["SPDXID"] = ["SPDXRef-" + package_dict["PackageName"][0]]
        if "Homepage" in control_dict:
            package_dict["PackageHomePage"] = control_dict["Homepage"]
        package_dict["PackageComment"] = control_dict["Description"]

        # クリエーション情報の追加・修正
        cre_dict = tv_dict["Creation Information"][0]
        cre_dict["Creator"].append("Tool: spdx_transitive")
        cre_dict["Creator"].append("Person: " + auth_name)
        
        # ドキュメント情報の追加・修正
        doc_dict = tv_dict["Document Information"][0]
        doc_dict["DocumentName"] = [control_dict["Package"][0] + "_" + control_dict["Version"][0]]
        # created と packagename と versionから生成(グローバルに参照できるアドレスがある方が望ましい)
        doc_dict["DocumentNamespace"] = [
            "http://spdx.org/spdxdocs/"
            + doc_dict["DocumentName"][0]
            + "-"
            + str(uuid.uuid5(uuid.NAMESPACE_URL, (doc_dict["DocumentName"][0] + cre_dict["Created"][0])))
        ]
        doc_dict["Relationship"] = [doc_dict["SPDXID"][0] + " DESCRIBES " + package_dict["SPDXID"][0]]
        # 保留
        # doc_dict["DocumentNamespace"] = ["文章"]

        # ファイルパス と SPDXID の修正 と Relationship の追加
        for i, file_dict in enumerate(tv_dict["File"]):
            file_dict["FileName"] = [file_dict["FileName"][0].replace(("./" + package_dict["PackageName"][0]), '', 1)]
            file_dict["SPDXID"] = ["SPDXRef-" + package_dict["PackageName"][0] + "_file_" + str(i)]
            file_dict["Relationship"] = [package_dict["SPDXID"][0] + " CONTAINS " + file_dict["SPDXID"][0]]

        tv_dict["Extracted License"] = self.rm_license_dup(tv_dict["Extracted License"])
        

    def add_relationship(self):
        print(4)

    def run(self, package_name: str, auth_name: str, trail_list: list[str]) -> list[str]:
        """
        DebianパッケージのSPDXを推移的に生成

        Args: 
            package_name(str): 対象パッケージ
            auth_name(str): 作者名
            trail_list(list[str]): 辿ってきた依存関係
        
        Returns:
            list[str]: 相互依存先パッケージ名のリスト
        """
        print(package_name, "enter")
        # 既に存在しているとき
        # if os.path.exists(package_name + ".json"):

        package_status = subprocess.run(
            ["dpkg-query", "-s", package_name], capture_output=True, text=True
        ).stdout.strip()
        self.control_dict = control_to_dict.control_to_dict(package_status)
        

        # 作業用ディレクトリの作成
        # ファイルの展開とtvファイルの生成をするディレクトリ
        os.mkdir(package_name)
        os.chdir(package_name)
        print(os.getcwd())
        dpkg_L_list = subprocess.run(
            ["dpkg", "-L", package_name], capture_output=True, text=True
        ).stdout.splitlines()
        for value in dpkg_L_list:
            if os.path.isdir(value):
                dirname = package_name + value
                os.makedirs(dirname, exist_ok=True)
            else:
                shutil.copy2(value, dirname)

        output = "output.tag"
        subprocess.run(
            ["scancode", "-clpi", package_name, "--spdx-tv", output]
        )

        self.tv_dict = tv_to_dict.tv_to_dict(output)
        
        os.chdir("..")
        # 作業用ディレクトリの削除
        shutil.rmtree(package_name)

        print(package_name, "tv_to_dict")

        self.merge_tv_control(auth_name)

        spdx_text = dict_to_tv.dict_to_tv(self.tv_dict)

        # 依存関係解決 Todo
        Deb_Spdx

        with open(package_name + ".spdx", mode='w') as f:
            f.write(spdx_text)

        print(package_name, "finish")

        return []


