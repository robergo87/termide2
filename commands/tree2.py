# pylint: disable=C0116,C0115,C0114

from os import listdir, getcwd
from os.path import abspath, basename, isdir, exists, join as path_join
import subprocess
import json
import curses
from argparse import ArgumentParser, REMAINDER

from shared.sockets import call_gui
from shared.curses import Listing
import inotify.adapters

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("sid", type=str)
parser.add_argument("editor", type=str, nargs=REMAINDER)

# ######################################
# callbacks setup
# ######################################


class Tree(Listing):
    def __init__(self, root, sid, editor, indent=2, icon_opened="-", icon_closed="+"):
        super().__init__()
        self.root = root
        self.sid = sid
        self.editor = editor
        self.opened = set()
        self.indent = indent
        self.icon_opened = icon_opened
        self.icon_closed = icon_closed
        self.notify = inotify.adapters.Inotify()
        self.notify.add_watch(root)
        
    def call_space(self, *params):
        return subprocess.check_output(
            ["termide", "space", "--sid", self.sid] 
            + 
            list(params)
        )
        
    def file_line(self, flag, current, filename, indent):
        return {
            "indent": indent,
            "filename": filename,
            "rel": path_join(current, filename),
            "flag": flag
        }
        
    def generate_dir(self, current, indent):
        files, dirs = [], []
        dir_path = path_join(self.root, current)
        if not exists(dir_path):
            return []
        for filename in listdir(dir_path):
            file_path = path_join(dir_path, filename)
            if isdir(file_path):
               dirs.append(filename)
            else:
               files.append(filename) 
        dirs.sort()
        files.sort()
        for filename in dirs:
            relpath = path_join(current, filename)
            if relpath in self.opened:
                yield self.file_line("o", current, filename, indent)
                for subpath in self.generate_dir(relpath, indent+1):
                    yield subpath
            else:
                yield self.file_line("c", current, filename, indent)
        for filename in files:
            yield self.file_line("f", current, filename, indent)
        

    def generate(self):
        return list(self.generate_dir("", 0))

    def open_dir(self, filepath):
        self.opened.add(self.selected)
        full_path = path_join(self.root, self.selected)
        if exists(full_path):
            self.notify.add_watch(full_path)

    def close_dir(self, filepath):
        self.opened.remove(self.selected)
        full_path = path_join(self.root, self.selected)
        if exists(full_path):
            self.notify.remove_watch(full_path)

    
    def default_action(self):
        full_path = path_join(self.root, self.selected)
        if isdir(full_path):
            if self.selected in self.opened:
                self.close_dir(self.selected)
            else:
                self.open_dir(self.selected)
            self.update_data()
        else:
            return subprocess.check_output([
                "termide", "space", "reopen", "--focus", "1", 
                "--sid", "editor", "--tid", self.selected,
                "--cmd", "/usr/bin/micro", self.selected
            ])
 
    def draw_single_row(self, row, is_selected, printfunc):
        color = (
            curses.color_pair(1)
            if row["flag"] == "f" else
            curses.color_pair(2)
        )
        icon = " "
        if row["flag"] == "o":
            icon = self.icon_opened
        if row["flag"] == "c":
            icon = self.icon_closed
        printfunc(
            " {}{} {}".format(row["indent"]*self.indent*" ", icon, row["filename"]),
            color
        )      

    def row_key(self, row):
        return row["rel"]

    def refresh(self):
        #https://www.man7.org/linux/man-pages/man7/inotify.7.html
        types_for_update = set([
            "IN_CREATE", "IN_DELETE",
            "IN_CREATE_SELF", "IN_DELETE_SELF",
            "IN_MOVE_SELF", 
            "IN_MOVED_FROM", "IN_MODED_TO"
            
        ])
        for event in self.notify.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            
            if types_for_update.intersection( set(type_names) ):
                self.update_data()

def call_fm(action, selected):
    return subprocess.check_output([
        "termide", "popup",
        "termide", "fm", action, selected
    ])


def execute_cmd(params):
    tree = Tree(abspath(getcwd()), params.get("sid"), params.get("editor"))

    @tree.keybinding(["d", "D"])
    def callback(listing):
        return call_fm("delete", tree.selected)

    @tree.keybinding(["m", "M"])
    def callback(listing):
        return call_fm("rename", tree.selected)

    @tree.keybinding(["c", "C"])
    def callback(listing):
        return call_fm("copy", tree.selected)

    @tree.keybinding(["n", "N"])
    def callback(listing):
        return call_fm("touch", tree.selected)

    @tree.keybinding(["e", "E"])
    def callback(listing):
        return call_fm("echo", tree.selected)
                
    tree.run()
