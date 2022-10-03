from unicodedata import name
import deb

if __name__ == "__main__":
    PACKAGE_NAME = "slack-desktop"

    # 入力
    package_name = "xxd"
    deb_cl = deb.Spdx_Deb()
    deb_cl.set(package_name)
    deb_cl.run()

    # パッケージの種類判定

    