import json


def make_info_list(spdx_dict, line_iter):
    ##-------------------------
    ## Document Information
    ##-------------------------
    # のDocument Informationにあたる部分を取り出す
    new_info = next(line_iter)[3:]
    next(line_iter)
    # 新しいInfomationとして追加
    spdx_dict[new_info] = []
    return spdx_dict[new_info]


# tagとvalueに分割する
def split_tv(line, line_iter):
    if ": " not in line:
        print(line)
    tag, value = line.split(": ", 1)
    # valueが<text>すなわち複数行にまたがれる形式だった場合
    if value.strip().startswith("<text>"):
        for text in line_iter:
            value += "\n"
            value += text
            if "</text>" in text:
                break
    return tag, value


# tvSPDXを整形する（改良の余地あり(line in ["##File"]の部分)）
# 連続する空行と指定した文字列の行を削除する
def format_tv(lines):
    for i, line in enumerate(lines):
        if (not line.strip()) or (line in ["##File"]):
            while (i + 1 != len(lines)) and (
                (not lines[i + 1].strip()) or (lines[i + 1] in ["##File"])
            ):
                lines.pop(i)
    return lines


# TagValue形式のspdxをjson形式に変換
def tv_to_dict(spdxtv: str):
    elem_dict = {}
    info_list = [elem_dict]
    spdx_dict = {"preamble": info_list}

    # FOSSologyから受け取ったcopyrightのspdxを読む
    with open(spdxtv, mode="r", encoding="utf-8") as f:
        line_strip = [s.strip("\n") for s in f.readlines()]
        line_iter = iter(format_tv(line_strip))

    for line in line_iter:
        # 空行は新たな要素の書き出しと見る
        if not line.strip():
            elem_dict = {}
            info_list.append(elem_dict)
        # infomationの始まりは別処理
        elif line.startswith("##"):
            if elem_dict == {}:
                info_list.pop()
            info_list = make_info_list(spdx_dict, line_iter)
        # tag, valueの行の扱い
        else:
            tag, value = split_tv(line, line_iter)
            if tag in elem_dict:
                elem_dict[tag].append(value)
            else:
                elem_dict[tag] = [value]

    else:
        spdx_json = spdxtv.rsplit(".", 1)[0] + ".json"
        with open(spdx_json, mode="w", encoding="utf-8") as f:
            json.dump(spdx_dict, f, indent=4)
        return spdx_json