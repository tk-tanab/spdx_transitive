import platform
import subprocess
import scancode
import spdx
import os
import shutil
import uuid

package_name = "x   xd"

with open('output.tag', 'rb') as file:
    # ファイルを読み取る
    fileData = file.read()
print(fileData)

# os.mkdir(package_name)
# os.chdir(package_name)
# dpkg_L_list = subprocess.run(
#     ["dpkg", "-L", package_name], capture_output=True, text=True
# ).stdout.splitlines()
# for value in dpkg_L_list:
#     if os.path.isdir(value):
#         dirname = "." + value
#         os.makedirs(dirname, exist_ok=True)
#     else:
#         shutil.copy2(value, dirname)

# subprocess.run(
#     ["scancode", "-clpi", "./", "--spdx-tv", "output.tag"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
# )

# print("Success!!")