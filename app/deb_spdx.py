import subprocess
import os
import control_to_dict
import hashlib
import uuid
import dict_to_tv
import re
import glob
import make_tv_dict

class Deb_Spdx:

    pv_dict: dict[str, str] # {p_name: version}
    vrp_dict: dict[str, list[list[str]]] # {vrp_name: [[p_name, c_operator, version]]}
    tv_dict: dict[str, list[dict[str, list[str]]]] # SPDX.json 参照
    control_dict: dict[str, list[str]] # {field_name: [values]}
    package_name: str
    auth_name: str
    trail_list: list[str] # [p_name]
    treated_list = []

    def return_spdx(self):
        return self.tv_dict

    def __init__(self, pv_dict, vrp_dict, package_name, auth_name, trail_list: list[str]):
        self.pv_dict = pv_dict
        self.vrp_dict = vrp_dict
        self.tv_dict = {}
        self.control_dict = {}
        self.package_name = package_name
        self.auth_name = auth_name
        self.trail_list = trail_list.copy()

    def rm_license_dup(self, lic_dict_list):
        """
        未定義ライセンスの重複削除
        
        Args: 
            lic_dict_list(list[str]): 未定義ライセンスのリスト
        """
        lic_rm_dup_list = []
        for lic_dict in lic_dict_list:
            for lic_rm_dup in lic_rm_dup_list:
                if lic_rm_dup == lic_dict:
                    break
            else:
                lic_rm_dup_list.append(lic_dict)
        else:
            return lic_rm_dup_list

    def merge_tv_control(self):
        """
        spdxファイルにcontrolファイルの情報を結合
        パッケージ間の依存関係情報 以外を追加・修正
        """
        tv_dict = self.tv_dict
        control_dict = self.control_dict

        # 参照に不整合が生じる場合
        if control_dict["Package"][0] != self.package_name:
            print(control_dict["Package"][0], self.package_name, "Error")

        # パッケージ情報の追加・修正
        package_dict = tv_dict["Package"][0]
        package_dict["PackageName"] = control_dict["Package"]
        package_dict["PackageVersion"] = control_dict["Version"]
        package_dict["SPDXID"] = ["SPDXRef-" + package_dict["PackageName"][0].replace('+', '')]
        if "Homepage" in control_dict:
            package_dict["PackageHomePage"] = control_dict["Homepage"]
        package_dict["PackageComment"] = control_dict["Description"]
        package_dict["Relationship"] = []

        # クリエーション情報の追加・修正
        cre_dict = tv_dict["Creation Information"][0]
        cre_dict["Creator"].append("Tool: spdx_transitive")
        cre_dict["Creator"].append("Person: " + self.auth_name)
        
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
        doc_dict["ExternalDocumentRef"] = []
        doc_dict["Relationship"] = [doc_dict["SPDXID"][0] + " DESCRIBES " + package_dict["SPDXID"][0]]

        # 保留
        # doc_dict["DocumentNamespace"] = ["文章"]

        # ファイルパス と SPDXID の修正 と Relationship の追加
        for i, file_dict in enumerate(tv_dict["File"]):
            file_dict["FileName"] = [file_dict["FileName"][0].replace(("./" + package_dict["PackageName"][0]), '', 1)]
            file_dict["SPDXID"] = ["SPDXRef-" + package_dict["PackageName"][0] + "-file-" + str(i)]
            file_dict["Relationship"] = [package_dict["SPDXID"][0] + " CONTAINS " + file_dict["SPDXID"][0]]

        tv_dict["Extracted License"] = self.rm_license_dup(tv_dict["Extracted License"])
        

    def add_relationship(self, d_list: list[str])-> list[str]:
        pv_dict = self.pv_dict
        vrp_dict = self.vrp_dict
        mutual_list: list[str] = []
        package_dict = self.tv_dict["Package"][0]
        termed_d_list = []
        not_out_list = []

        dori_list = []
        for dp in d_list:
            or_list = dp.split(' | ')
            ori_list = []
            for d in or_list:
                ori_list.append([i for i in re.split(" |\(|\)|\[.*?\]|:any", d) if i])
            dori_list.append(ori_list)

        for ori_list in dori_list:
            for or_list in ori_list:
                if or_list[0] in pv_dict and self.check_version(or_list[1:], ["=", pv_dict[or_list[0]]]):
                    real_dp_name = or_list[0]
                    break

                elif or_list[0] in vrp_dict:
                    for real_p_list in vrp_dict[or_list[0]]:
                        if self.check_version(or_list[1:], real_p_list[1:]):
                            real_dp_name = real_p_list[0]
                            break
                    else:
                        continue
                    break
            else:
                continue
            
            # 同じ依存先を複数回指定または自分を依存先に指定しているとき
            if real_dp_name in termed_d_list or real_dp_name == self.package_name:
                continue
            else:
                termed_d_list.append(real_dp_name)
            
            # 既に存在しているとき
            if (spdx_p_name:=self.spdx_exists(real_dp_name)):
                print(real_dp_name, "already exist")
                self.add_external_ref(spdx_p_name)
            # このパッケージの別の枝(未出力)で調査済みのとき
            elif real_dp_name in not_out_list:
                package_dict["Relationship"].append(package_dict["SPDXID"][0] + " DEPENDS_ON SPDXRef-" + real_dp_name)
            # 上の階層のパッケージと相互依存になっているとき か すでに上の階層のパッケージの別の枝で調査済みのとき
            elif real_dp_name in self.trail_list or real_dp_name in self.treated_list:
                package_dict["Relationship"].append(package_dict["SPDXID"][0] + " DEPENDS_ON SPDXRef-" + real_dp_name)
                mutual_list.append(real_dp_name)
            else:
                snap_len_treated = len(self.treated_list)
                new_spdx = Deb_Spdx(pv_dict, vrp_dict, real_dp_name, self.auth_name, self.trail_list)
                r_mutual_list = new_spdx.run()
                print("back", self.package_name)

                # 下の階層のパッケージと相互依存になっているとき
                if r_mutual_list != []:
                    # relationship
                    package_dict["Relationship"].append(package_dict["SPDXID"][0] + " DEPENDS_ON SPDXRef-" + real_dp_name)
                    self.merge_spdx(new_spdx.return_spdx())
                    not_out_list += self.treated_list[snap_len_treated:]
                    mutual_list += [p for p in r_mutual_list if (p != self.package_name) and (p not in not_out_list)]
                # 問題なし
                else:
                    self.add_external_ref(real_dp_name)
        mutual_list = list(set(mutual_list))
        return mutual_list
    
    def spdx_exists(self, p_name):
        if p_name not in self.treated_list:
            return False
        if os.path.exists(p_name + ".spdx"):
            return p_name
        else:
            for spdx_path in glob.glob("*.spdx"):
                with open(spdx_path, mode="r", encoding="utf-8") as f:
                    lines_strip = [s.strip() for s in f.readlines()]
                for line in lines_strip:
                    if ("PackageName: " + p_name) == line.strip():
                        flag = True
                        break
                    elif "## File" == line.strip():
                        flag = False
                        break
                if flag:
                    break
            else:
                return False
            return spdx_path[:-5]
                    

    def add_external_ref(self, p_name: str):
        spdx_path = p_name + ".spdx"
        with open(spdx_path, mode="r", encoding="utf-8") as f:
            lines_strip = [s.strip() for s in f.readlines()]
        for line in lines_strip:
            if "DocumentNamespace" in line:
                ref_space = line[19:]
                break
        else:
            return

        with open(spdx_path, mode="rb") as f:
            file_data = f.read()
        hash_sha1 = hashlib.sha1(file_data).hexdigest()
        exd_list = self.tv_dict["Document Information"][0]["ExternalDocumentRef"]
        pac_dict = self.tv_dict["Package"][0]

        # DocumentRef-hello-go-src https://swinslow.net/spdx-examples/example6/hello-go-src-v2 SHA1: b3018ddb18802a56b60ad839c98d279687b60bd6
        # Relationship: SPDXRef-hello-go-binary GENERATED_FROM DocumentRef-hello-go-src:SPDXRef-Makefile
        doc_ref = "DocumentRef-" + p_name
        exd_list.append(doc_ref + ' ' + ref_space + ' SHA1: ' + hash_sha1)
        pac_dict["Relationship"].append((pac_dict["SPDXID"][0] + " DEPENDS_ON " + doc_ref + ":SPDXRef-" + p_name))

    def merge_spdx(self, dep_tv_dict):
        self.tv_dict["Document Information"][0]["ExternalDocumentRef"] = list(set(self.tv_dict["Document Information"][0]["ExternalDocumentRef"] + dep_tv_dict["Document Information"][0]["ExternalDocumentRef"]))
        self.tv_dict["Package"] += dep_tv_dict["Package"]
        self.tv_dict["File"] += dep_tv_dict["File"]
        self.tv_dict["Extracted License"] += dep_tv_dict["Extracted License"]
        self.tv_dict["Extracted License"] = self.rm_license_dup(self.tv_dict["Extracted License"])


    def compare_version(self, v1, v2, c_operator)-> bool:
        try:
            subprocess.run(
                ["dpkg", "--compare-versions", v1, c_operator, v2], check=True
            )
        except subprocess.CalledProcessError as e:
            return False
        return True

    def check_version(self, term_list, cond_list)-> bool:
        if term_list == []:
            return True
        elif cond_list == []:
            return False

        if term_list[0] == '=':
            match cond_list[0]:
                case '=':
                    co = 'eq'
                case '<=':
                    co = 'le'
                case '>=':
                    co = 'ge'
                case '<<':
                    co = 'lt'
                case _:
                    co = 'gt'
        elif term_list[0] == '<=':
            if cond_list[0] == '=' or cond_list[0] == '>=':
                co = "ge"
            elif cond_list[0] == '>>':
                co = "gt"
            else:
                return True
        elif term_list[0] == '>=':
            if cond_list[0] == '=' or cond_list[0] == '<=':
                co = "le"
            elif cond_list[0] == '<<':
                co = "lt"
            else:
                return True
        elif term_list[0] == '<<':
            if cond_list[0] == '<=' or cond_list[0] == '<<':
                return True
            else:
                co = "gt"
        else:
            if cond_list[0] == '>=' or cond_list[0] == '>>':
                return True
            else:
                co = "lt"

        return self.compare_version(term_list[1], cond_list[1], co)
                

    def run(self, mode=0) -> list[str]:
        """
        DebianパッケージのSPDXを推移的に生成

        Args: 
            package_name(str): 対象パッケージ
            auth_name(str): 作者名
            trail_list(list[str]): 辿ってきた依存関係
        
        Returns:
            list[str]: 相互依存先パッケージ名のリスト
        """
        # 0: 最初のパッケージだけライセンス(c)
        # 1: すべてのパッケージライセンス(c)
        # 2: すべてのパッケージライセンス(a)
        # 3: ライセンスは確認しない、ファイルもしない
        
        package_name = self.package_name
        self.trail_list.append(package_name)
        print(package_name, "enter")

        package_status = subprocess.run(
            ["dpkg-query", "-s", package_name], capture_output=True, text=True
        ).stdout.strip()
        self.control_dict = control_to_dict.control_to_dict(package_status)
        
        if mode == 0:
            if len(self.treated_list) == 0:
                self.tv_dict = make_tv_dict.make_tv_dict(package_name, 0)
            else:
                self.tv_dict = make_tv_dict.make_tv_dict(package_name, 1)
        elif mode == 1:
            self.tv_dict = make_tv_dict.make_tv_dict(package_name, 0)
        elif mode == 2:
            self.tv_dict = make_tv_dict.make_tv_dict(package_name, 2)
        else:
            self.tv_dict = make_tv_dict.make_tv_dict(package_name, 3)

        self.treated_list.append(package_name)

        self.merge_tv_control()

        mutual_list = self.add_relationship(self.control_dict["Depends"])

        spdx_text = dict_to_tv.dict_to_tv(self.tv_dict)

        if mutual_list == []:
            with open(package_name + ".spdx", mode='w') as f:
                f.write(spdx_text)
            print(package_name, "finish")

        return mutual_list


