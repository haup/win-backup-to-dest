""" Windows Backup a folder to Destination """

import sys
import subprocess
import shutil
import os
from datetime import datetime
import logging
import re


SHARE = r"\\saiken\backup\wtd"
LETTER = "Z:"


def _logpath(path, names):
    logging.info('Working in %s', path)
    return []   # nothing will be ignored


def check_if_folder_is_nuendo_project(dir):
    dir_list = os.listdir(dir) 
    regex = re.compile('[a-zA-Z0-9]*.npr')
    if any(regex.match(item) or (os.path.isdir(item) and item == "Audio") for item in dir_list):
        return True
    return False


def copytree(src, dst, symlinks=False, ignore=_logpath):
    """ copytree from https://stackoverflow.com/questions/1868714/
    how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth """
    folders = ()
    try:
        folders = os.listdir(src)
    except OSError as error:
        print('%s', error)
        return
    for item in folders:
        source = os.path.join(src, item)
        destination = os.path.join(dst, item)
        if symlinks and os.path.islink(source):
            linkto = os.readlink(source)
            os.symlink(linkto, destination)
        elif os.path.isdir(source):
            print(source)
            try:
                shutil.copytree(source, destination, symlinks, ignore)
            except shutil.Error as error:
                print('Directory not copied. Error: %s', error)
            except OSError as error:
                print('Directory not copied. Error: %s', error)
        else:
            print(source)
            try:
                shutil.copy2(source, destination)
            except shutil.SameFileError as sfe:
                print("File alread there! Error: ", sfe)
                continue
            except shutil.Error as error:
                print('Directory not copied. Error: ', error)
            except OSError as error:
                print('Directory not copied. Error: ', error)


def mount_share():
    subprocess.check_call(["net", "use", LETTER, SHARE],
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def umount_share():
    subprocess.check_call(["net", "use", LETTER, "/delete", "/yes"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def assemble_destination(path):
    return os.path.join(LETTER + "\\", path.split("\\")[-1] + "\\" + 
                        str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))


def copy_nuendo_files(path, destination):
    dir_list = os.listdir(path)
    print(dir_list)
    regex = re.compile('[a-zA-Z0-9]*.npr')
    npr_list = [regex.match(item) for item in dir_list]
    print(npr_list)
    os.makedirs(destination, exist_ok=True)
    for item in dir_list:
        print(item)
        if regex.match(item):
            shutil.copy2(os.path.join(path + "\\" + item), destination + "\\")
    os.makedirs(destination + "\\" + "Audio", exist_ok=True)
    copytree(os.path.join(path + "\\" + "Audio"),
             os.path.join(destination + "\\" + "Audio"))
    if os.path.exists(os.path.join(path + "\\" + "Edits")):
        os.makedirs(destination + "\\" + "Edits", exist_ok=True)
        copytree(os.path.join(path + "\\" + "Edits"),
                 os.path.join(destination + "\\" + "Edits"))


def main(argv):
    """ Main function """
    path = ' '.join(argv[1:])
    if not check_if_folder_is_nuendo_project(path):
        input("This is not an Nuendo project, please use one of those")
        return 0
    destination = assemble_destination(path)
    if LETTER in str(subprocess.check_output(["net", "use"])):
        print("Network drive still mounted")
        umount_share()
    mount_share()
    if not os.path.exists(destination):
        copy_nuendo_files(path, destination)
    else: 
        print("folder is already there")
    umount_share()


if __name__ == "__main__":
    try:
        main(sys.argv)
    except:
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())
    finally:
        print("Press Enter to continue ...")
        input()
