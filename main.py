""" Windows Backup a folder to Destination """

import sys
import subprocess
import shutil
import os
from datetime import date
import logging

SHARE = r"\\192.168.1.65\backup"
LETTER = "Z:"


def _logpath(path, names):
    logging.info('Working in %s', path)
    return []   # nothing will be ignored


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


def main(argv):
    """ Main function """
    path = argv[1]
    destination = os.path.join(LETTER + "\\", path.split("\\")[-1] + "-" + str(date.today()))
    if LETTER in str(subprocess.check_output(["net", "use"])):
        print("Network drive still mounted")
        subprocess.check_call(["net", "use", LETTER, "/delete", "/yes"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    subprocess.check_call(["net", "use", LETTER, SHARE],
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if os.path.isdir(destination) is not True:
        copytree(path, destination)
    else: 
        print("folder is already there")
    subprocess.check_call(["net", "use", LETTER, "/delete", "/yes"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


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
