""" Windows Backup a folder to Destination """

import sys
import subprocess
import shutil
import os
from datetime import datetime
import logging
import re
import json


SHARE = r""
LETTER = ""


def join_list_with_seperator(iterator, seperator):
    it = map(str, iterator)
    seperator = str(seperator)
    string = next(it, '')
    for s in it:
        string += seperator + s
    return string


def load_config():
    global LETTER
    global SHARE
    try:
        with open(os.getenv('SystemDrive') + os.sep + 'win-backup-to-dest' + os.sep + 'config.json') as json_data_file:
            data = json.load(json_data_file)
        SHARE, LETTER = data["server"].values()
        SHARE = os.sep + join_list_with_seperator(SHARE.split("/"), os.sep)
    except OSError:
        print("Cannot load config file")
        return


def _logpath(path, names):
    logging.info('Working in %s', path)
    return []   # nothing will be ignored


def check_file_smaller_than_50_mb(file):
        size = os.path.getsize(file)
        mb_size = round(size / 1024 / 1024, 3)
        if mb_size < 50:
            return True
        return False


def check_if_folder_is_nuendo_project(dir):
    dir_list = os.listdir(dir) 
    regex = re.compile('[a-zA-Z0-9- _.:?!()&`´^äöüß+#@=;,]*.npr')
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
                if check_file_smaller_than_50_mb(source):
                    shutil.copy2(source, destination)
                else:
                    continue
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
    folders = list(filter(None, path.split(os.sep)[1:]))
    folders_path = ""
    for item in folders:
        folders_path = folders_path + item + os.sep
    return os.path.join(LETTER + os.sep + folders_path + 
                        str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))


def copy_nuendo_files(path, destination):
    audio_string = os.sep + "Audio"
    edits_string = os.sep + "Edits"
    dir_list = os.listdir(path)
    regex = re.compile('.npr$|.bak$')
    os.makedirs(destination, exist_ok=True)
    for item in dir_list:
        print(item)
        if regex.search(item):
            shutil.copy2(os.path.join(path + os.sep + item), destination + os.sep)
    os.makedirs(destination + audio_string, exist_ok=True)
    copytree(os.path.join(path + audio_string),
             os.path.join(destination + audio_string))
    if os.path.exists(os.path.join(path + edits_string)):
        os.makedirs(destination + edits_string, exist_ok=True)
        copytree(os.path.join(path + edits_string),
                 os.path.join(destination + edits_string))


def main(argv):
    """ Main function """
    path = ' '.join(argv[1:])
    if not check_if_folder_is_nuendo_project(path):
        input("This is not an Nuendo project, please use one of those")
        return 0
    load_config()
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
