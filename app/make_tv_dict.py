import os
from pprint import pprint
import subprocess
import shutil
import tv_to_dict
import hashlib
from datetime import datetime

# 0: copyrightだけライセンス+ファイル
# 1: すべてのファイルのライセンスなし
# 2: 全てのファイルのライセンス
# 3: ライセンスは確認しない、ファイルもしない

def make_tv_dict(package_name, mode):
    template_tv_dict: dict[str, list[dict[str, list[str]]]] = {
        "Document Information": [
            {
                "SPDXVersion": [],
                "DataLicense": [],
                "DocumentNamespace": [],
                "DocumentName": [],
                "SPDXID": ["SPDXRef-DOCUMENT"],
                "DocumentComment": [],
                "ExternalDocumentRef": [],
                "Relationship": []
            }
        ],
        "Creation Information": [
            {
                "Creator": [],
                "Created": [datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')]
            }
        ],
        "Package": [
            {
                "PackageName": [],
                "PackageVersion": [],
                "SPDXID": [],
                "PackageDownloadLocation": ["NOASSERTION"],
                "PackageVerificationCode": [],
                "PackageLicenseDeclared": ["NOASSERTION"],
                "PackageLicenseConcluded": ["NOASSERTION"],
            }
        ],
        "File": [
        ],
        "Extracted License": [
        ]
    }

    if mode == 3:
        template_tv_dict["Package"][0]["FilesAnalyzed"] = ["false"]
        return template_tv_dict

    # 作業用ディレクトリの作成
    # ファイルの展開とtvファイルの生成をするディレクトリ
    os.mkdir(package_name)
    dpkg_L_list = subprocess.run(
        ["dpkg", "-L", package_name], capture_output=True, text=True
    ).stdout.splitlines()

    if mode == 0:

        hash_list = []
        file_dict_list = []

        for value in dpkg_L_list:
            if os.path.isfile(value):
                if value.endswith("copyright"):
                    copyright_filepath = value
                    try:
                        shutil.copyfile(value, package_name+'/copyright')
                    except (FileNotFoundError, PermissionError):
                        pass
                try:
                    with open(value, mode="rb") as f:
                        file_data = f.read()
                    hash_sha1 = hashlib.sha1(file_data).hexdigest()
                    hash_list.append(hash_sha1)
                    if not value.endswith("copyriht"): 
                        file_dict = {
                            "FileName": [value],
                            "SPDXID": [],
                            "FileChecksum": ["SHA1: " + hash_sha1],
                            "LicenseConcluded": ["NOASSERTION"],
                            "LicenseInfoInFile": ["NOASSERTION"],
                            "FileCopyrightText": ["NOASSERTION"]
                        }
                        file_dict_list.append(file_dict)
                except (FileNotFoundError, PermissionError):
                    pass
        else:
            hash_list.sort()
                
        output = package_name + "/output.tag"
        # , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        subprocess.run(
            ["scancode", "-clpi", package_name, "--spdx-tv", output], stdout=subprocess.PIPE
        )

        tv_dict = tv_to_dict.tv_to_dict(output)
        tv_dict["Package"][0].update({"PackageVerificationCode": [hashlib.sha1("".join(hash_list).encode("utf-8")).hexdigest()]})
        tv_dict["File"] += file_dict_list
        tv_dict["File"][0].update({"FileName": [copyright_filepath]})

    elif mode == 1:

        hash_list = []
        file_dict_list = []

        for value in dpkg_L_list:
            if os.path.isfile(value):
                try:
                    with open(value, mode="rb") as f:
                        file_data = f.read()
                    hash_sha1 = hashlib.sha1(file_data).hexdigest()
                    hash_list.append(hash_sha1)
                    file_dict = {
                        "FileName": [value],
                        "SPDXID": [],
                        "FileChecksum": ["SHA1: " + hash_sha1],
                        "LicenseConcluded": ["NOASSERTION"],
                        "LicenseInfoInFile": ["NOASSERTION"],
                        "FileCopyrightText": ["NOASSERTION"]
                    }
                    file_dict_list.append(file_dict)
                except (FileNotFoundError, PermissionError):
                    pass
        else:
            hash_list.sort()

        tv_dict = template_tv_dict
        tv_dict["Package"][0].update({"PackageVerificationCode": [hashlib.sha1("".join(hash_list).encode("utf-8")).hexdigest()]})
        tv_dict["File"] += file_dict_list

    elif mode == 2:
        for value in dpkg_L_list:
            if os.path.isdir(value):
                dirname = package_name + value
                os.makedirs(dirname, exist_ok=True)
            else:
                try:
                    shutil.copyfile(value, package_name+value)
                except (FileNotFoundError, PermissionError):
                    pass

        output = package_name + "/output.tag"
        # , stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        subprocess.run(
            ["scancode", "-clpi", package_name, "--spdx-tv", output], stdout=subprocess.PIPE
        )

        tv_dict = tv_to_dict.tv_to_dict(output)

    # 作業用ディレクトリの削除
    shutil.rmtree(package_name)

    return tv_dict