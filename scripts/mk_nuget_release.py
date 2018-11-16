# 
# Copyright (c) 2018 Microsoft Corporation
#

# 1. download releases from github
# 2. copy over libz3.dll for the different architectures
# 3. copy over Microsoft.Z3.dll from suitable distribution
# 4. copy nuspec file from packages
# 5. call nuget pack

import json
import os
import urllib.request
import zipfile
import sys
import os.path
import shutil
import subprocess
import mk_util
import mk_project

data = json.loads(urllib.request.urlopen("https://api.github.com/repos/Z3Prover/z3/releases/latest").read().decode())

version_str = data['tag_name']

def mk_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

def download_installs():
    for asset in data['assets']:
        url = asset['browser_download_url']
        name = asset['name']
        if "x64" not in name:
            continue
        print("Downloading ", url)
        sys.stdout.flush()
        urllib.request.urlretrieve(url, "packages/%s" % name)

os_info = {"ubuntu-14" : ('so', 'ubuntu.14.04-x64'),
           'ubuntu-16' : ('so', 'ubuntu.16.04-x64'),
           'win' : ('dll', 'win-x64'),
           'debian' : ('so', 'debian.8-x64') }

def classify_package(f):
    for os_name in os_info:
        if os_name in f:
            ext, dst = os_info[os_name]
            return os_name, f[:-4], ext, dst
    return None
        
def unpack():
    # unzip files in packages
    # out
    # +- runtimes
    #    +- win-x64
    #    +- ubuntu.16.04-x64
    #    +- ubuntu.14.04-x64
    #    +- debian.8-x64
    # +
    for f in os.listdir("packages"):        
        if f.endswith("zip") and "x64" in f and classify_package(f):
            print(f)
            os_name, package_dir, ext, dst = classify_package(f)                        
            zip_ref = zipfile.ZipFile("packages/%s" % f, 'r')
            zip_ref.extract("%s/bin/libz3.%s" % (package_dir, ext), "tmp")
            mk_dir("out/runtimes/%s" % dst)
            shutil.move("tmp/%s/bin/libz3.%s" % (package_dir, ext), "out/runtimes/%s/." % dst)
            if "win" in f:
                mk_dir("out/lib/netstandard1.0/")
                for b in ["Microsoft.Z3.dll"]:
                    zip_ref.extract("%s/bin/%s" % (package_dir, b), "tmp")
                    shutil.move("tmp/%s/bin/%s" % (package_dir, b), "out/lib/netstandard1.0/%s" % b)

def create_nuget_spec():
    mk_project.init_version()
    contents = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2010/07/nuspec.xsd">
    <metadata>
        <id>Microsoft.Z3.x64</id>
        <version>%s</version>
        <authors>Microsoft</authors>
        <description>Z3 is a satisfiability modulo theories solver from Microsoft Research.</description>
        <copyright>Copyright Microsoft Corporation. All rights reserved.</copyright>
        <tags>smt constraint solver theorem prover</tags>
        <iconUrl>https://raw.githubusercontent.com/Z3Prover/z3/master/package/icon.jpg</iconUrl>
        <projectUrl>https://github.com/Z3Prover/z3</projectUrl>
        <licenseUrl>https://raw.githubusercontent.com/Z3Prover/z3/master/LICENSE.txt</licenseUrl>
        <repository
            type="git"
            url="https://github.com/Z3Prover/z3.git"
            branch="master"
        />
        <requireLicenseAcceptance>true</requireLicenseAcceptance>
        <language>en</language>
    </metadata>
</package>"""

    with open("out/Microsoft.Z3.x64.nuspec", 'w') as f:
        f.write(contents % mk_util.get_version_string(3))

def create_nuget_package():
    subprocess.call(["nuget", "pack"], cwd="out")

def main():
    mk_dir("packages")
    download_installs()
    unpack()
    create_nuget_spec()
    create_nuget_package()


main()
