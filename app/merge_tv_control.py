import hashlib
import uuid


def merge_tv_control(tv_dict: dict[str, list[dict[str, list[str]]]], control_dict: dict[str, list[str]], namespace_dict: dict[str, str]) -> dict[str, list[dict[str, list[str]]]]:
    add_control_info(tv_dict, control_dict)
    # 依存関係の記述
    relationship_list = []
    tv_dict["Relationships"] = [{"Relationships": relationship_list}]
    relationship_list.append(tv_dict["Document Information"][0]["SPDXID"] + " DESCRIBES " + tv_dict["Package"][0]["SPDXID"])
    
    external_document_list = []
    tv_dict["Document Information"][0]["ExternalDocumentRef"] = external_document_list
    for depend_package in control_dict["Depends"]:
        with open('ファイル名', 'rb') as file:
            # ファイルを読み取る
            fileData = file.read()
        hash_sha1 = hashlib.sha1(fileData).hexdigest()
        

# spdxファイルにcontrolファイルの情報を結合
def add_control_info(spdx_dict, control_dict):
    spdx_dict["Document Information"][0]["DocumentName"] = [
        control_dict["PackageName"][0] + "_" + control_dict["PackageVersion"][0]
    ]
    # created と packagename と versionから生成
    spdx_dict["Document Information"][0]["DocumentNamespace"] = [
        "http://spdx.org/spdxdocs/"
        + spdx_dict["Document Information"][0]["DocumentName"][0]
        + "-"
        + str(uuid.uuid5(uuid.NAMESPACE_URL, (spdx_dict["Document Information"][0]["DocumentName"] + spdx_dict["Creation Info"][0]["Created"])))
    ]
    spdx_dict["Package Information"][0]["PackageName"] = control_dict["Package"]
    spdx_dict["Package Information"][0]["PackageVersion"] = control_dict["Version"]
    spdx_dict["Package Information"][0]["SPDXID"] = "SPDXRef-" + control_dict["Package"]
    spdx_dict["Package Information"][0]["PackageComment"] = control_dict["Description"]