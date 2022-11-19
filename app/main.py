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

if __name__ == "__main__":
    PACKAGE_NAME = "slack-desktop"

    # 入力
    package_name = "xxd"
    deb_cl = deb.Spdx_Deb()
    deb_cl.set(package_name)
    deb_cl.run()

    # パッケージの種類判定 todo
    # debianの事前処理

