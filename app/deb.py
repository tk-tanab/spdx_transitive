from genericpath import isdir
import shutil
import subprocess
import os
import control_to_dict
from macpath import dirname

class spdx_deb:

    main_package: str = "" # SPDXを生成するルートのパッケージ
    package_version: str = "" # main_packageのバージョン
    installed_list: list[str] = [] # インストール済パッケージ群

    def print_var(self):
        print(self.main_package)
        print(self.installed_list)
        print(self.package_version)


    def set(self, package_name: str) -> bool:
        """
        class全体で参照するものの作成

        Args: 
            package_name(str): 対象パッケージ
        Returns:
            bool: パッケージが存在するか
        """
        self.main_package = package_name
        self.installed_list = subprocess.run(
            ["apt", "list", "--installed"], capture_output=True, text=True
        ).stdout.splitlines()
        self.package_version = self.get_version(package_name)

        if self.package_version is None:
            print("This package has not been installed")
            return False
        return True

    
    def get_version(self, package_name: str) -> str:
        """
        パッケージのバージョンを取得
        Args: 
            package_name(str): 対象パッケージ
        Returns:
            str: パッケージのバージョン or None
        """
        for package in self.installed_list:
            if package.startswith(package_name + "/"):
                return package.split()[1]
        else:
            return None


    def run(self):
        """
        ディレクトリを移動
        SPDX群を入れるディレクトリの作成
        SPDXの推移的な生成
        """
        cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__) + "/..")
        # すでに同名のSPDXがある場合はエラー出力
        # 完全に同名の複数バージョンはない
        # バージョン名をディレクトリ名に加える
        dir_name = "SPDX/" + self.main_package + "_" + self.package_version
        try:
            os.makedirs(dir_name)
            os.chdir(dir_name)
        except FileExistsError:
            print("That SPDX already exists")
            return

        self.make_spdx_transitive(self.main_package)
        os.chdir(cwd)


    def make_spdx_transitive(self, package_name: str) -> bool:
        """
        DebianパッケージのSPDXを推移的に生成

        Args: 
            package_name(str): 対象パッケージ
        
        Returns:
            bool: SPDXを生成したか
        """
        # 既に存在しているとき
        if os.path.exists(package_name + ".spdx"):
            return True

        package_showlist = subprocess.run(
            ["apt", "show", package_name, "-a"], capture_output=True, text=True
        ).stdout.split("\n\n")

        package_version = self.get_version(package_name)
        if package_version is None:
            return False

        for control in package_showlist:
            if ("Version: " + package_version + "\n") in control:
                control_dict = control_to_dict.control_to_dict(control)
                break
            else:
                # 該当するバージョンが見つからないときの処理
                print("Version:", package_version, "does not exist")

        # パッケージが存在するがバージョン的に依存していないものはどうする？(未実装)
        # 依存関係にあるものを洗い出す
        for depend_package in control_dict["Depends"]:
            if not self.make_spdx_transitive(depend_package):
                control_dict["Depends"].remove(depend_package)
        
        # 作業用ディレクトリの作成
        os.mkdir(package_name)
        os.chdir(package_name)
        dpkg_L_list = subprocess.run(
            ["dpkg", "-L", package_name], capture_output=True, text=True
        ).stdout.splitlines()
        for value in dpkg_L_list:
            if os.path.isdir(value):
                dirname = "." + value
                os.makedirs(dirname)
            else:
                shutil.copy2(value, dirname)

        subprocess.run(
            ["scancode", "-clpi", "./", "--spdx-tv", "output.tag"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )




