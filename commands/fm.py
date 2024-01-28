import readline
from os.path import basename, dirname, abspath, exists, isdir
from os import remove
from shutil import move as rename, copy2 as copy, rmtree, copytree 
from argparse import ArgumentParser, REMAINDER

def prefilled_input(prompt, initial=''):
    readline.set_startup_hook(lambda: readline.insert_text(initial))
    try:
        response = input(prompt)
    finally:
        readline.set_startup_hook(None)
    return response

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("action", type=str)
parser.add_argument("file", type=str)


def pressanykey():
    input("Press enter to continue ...")

def execute_rename(params):
    srcfile = params.get("file")
    dstfile = prefilled_input(" Rename file:\n ", srcfile)
    if not dstfile or srcfile == dstfile:
        return False
    if not exists(srcfile):
        print(f"File {srcfile} does not exists")
        return pressanykey()
    if exists(dstfile):
        print(f"File {dstfile} already exists")
        return pressanykey()
    try:
        rename(srcfile, dstfile)
    except Exception as e:
        print(str(e))
        return pressanykey()
    
def execute_copy(params):
    srcfile = params.get("file")
    dstfile = prefilled_input(" Copy file:\n ", srcfile)
    if not dstfile or srcfile == dstfile:
        return False
    if not exists(srcfile):
        print(f"Path {srcfile} does not exists")
        return pressanykey()
    if exists(dstfile):
        print(f"Path {dstfile} already exists")
        return pressanykey()
    try:
        if isdir(srcfile):
            copytree(srcfile, dstfile)
        else:
            copy(srcfile, dstfile)
    except Exception as e:
        print(str(e))
        return pressanykey()

def execute_delete(params):
    srcfile = params.get("file")
    answer = input("Confirm removing:\n{srcfile}\n(Y/N)").lower().strip()
    if answer != "y":
        return False
    if not exists(srcfile):
        print(f"Path {srcfile} does not exists")
        return pressanykey()
    try:
        if isdir(srcfile):
            rmtree(srcfile)
        else:
            remove(srcfile)
    except Exception as e:
        print(str(e))
        return pressanykey()

def execute_touch(params):
    srcfile = params.get("file")
    if not exists(srcfile):
        print(f"Path {srcfile} does not exists")
        return pressanykey()
    directory = srcfile if isdir(srcfile) else dirname(srcfile)
    if directory[-1] != "/":
        directory += "/" 
    dstfile = prefilled_input(" New file:\n ", directory)
    if exists(dstfile):
        print(f"Path {dstfile} already exists")
        return pressanykey()
    try:
        open(dstfile,"w").close()        
    except Exception as e:
        print(str(e))
        return pressanykey()

def execute_echo(params):
    srcfile = params.get("file")
    print(srcfile)
    return pressanykey()

def execute_cmd(params):
    action = params.get("action")
    if action == "echo":
        return execute_echo(params)
    if action == "touch":
        return execute_touch(params)
    if action == "rename":
        return execute_rename(params)
    if action == "copy":
        return execute_copy(params)
    if action == "delete":
        return execute_delete(params)

