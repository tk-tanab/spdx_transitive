import hashlib
import uuid


def merge_tv_control(tv_dict: dict[str, list[dict[str, list[str]]]], control_dict: dict[str, list[str]], space_ref_dict: dict[str, list[str]]) -> dict[str, list[dict[str, list[str]]]]:
    add_control_info(tv_dict, control_dict)
    # 依存関係の記述
    relationship_list = []
    tv_dict["Relationships"] = [{"Relationships": relationship_list}]
    relationship_list.append(tv_dict["Document Information"][0]["SPDXID"][0] + " DESCRIBES " + tv_dict["Package"][0]["SPDXID"][0])
    
    external_document_list = []
    tv_dict["Document Information"][0]["ExternalDocumentRef"] = external_document_list
    for depend_package in control_dict["Depends"]:
        with open(depend_package + '.json', 'rb') as file:
            # ファイルを読み取る
            fileData = file.read()
        hash_sha1 = hashlib.sha1(fileData).hexdigest()
        doc_ref = "DocumentRef-" + depend_package
        external_document_list.append(doc_ref + " " + space_ref_dict[depend_package][0] + " SHA1: " + hash_sha1)
        relationship_list.append(tv_dict["Package Information"][0]["SPDXID"][0] + " DEPENDS_ON " + doc_ref + ":" + space_ref_dict[depend_package][1])
    else:
        # 順番入れ替え
        tv_dict["Extracted Licenses"] = tv_dict.pop("Extracted Licenses")
        tv_dict["File"] = tv_dict.pop("File")
        

# spdxファイルにcontrolファイルの情報を結合
def add_control_info(spdx_dict: dict[str, list[dict[str, list[str]]]], control_dict: dict[str, list[str]]):
    spdx_dict["Document Information"][0]["DocumentName"] = [
        control_dict["Package"][0] + "_" + control_dict["Version"][0]
    ]
    # created と packagename と versionから生成(もちろんグローバルに参照できるアドレスがある方が望ましい)
    spdx_dict["Document Information"][0]["DocumentNamespace"] = [
        "http://spdx.org/spdxdocs/"
        + spdx_dict["Document Information"][0]["DocumentName"][0]
        + "-"
        + str(uuid.uuid5(uuid.NAMESPACE_URL, (spdx_dict["Document Information"][0]["DocumentName"][0] + spdx_dict["Creation Info"][0]["Created"][0])))
    ]
    spdx_dict["Package"][0]["PackageName"] = control_dict["Package"]
    spdx_dict["Package"][0]["PackageVersion"] = control_dict["Version"]
    spdx_dict["Package"][0]["SPDXID"] = ["SPDXRef-" + control_dict["Package"][0]]
    spdx_dict["Package"][0]["PackageComment"] = control_dict["Description"]