# pylint: disable=C0116,C0115,C0114
from os.path import dirname, basename, abspath, isdir, join as path_join
import os

import curses
from argparse import ArgumentParser, REMAINDER


class TreeListing:
    def __init__(self, root_dir, **kwargs):
        self.root_dir = abspath(root_dir)
        self.opened = set([self.root_dir])
        self.show_hidden = False
        self.indent = 2
        self.dir_closed_icon = "+"
        self.dir_opened_icon = "-"

        for key, value in kwargs.items():
            if not hasattr(self, key):
                continue
            setattr(self, key, value)

    def open(self, dirpath):
        full_path = path_join(self.root_dir, dirpath)
        self.opened.add(full_path)

    def close(self, dirpath):
        full_path = path_join(self.root_dir, dirpath)
        if full_path in self.opened:
            self.opened.remove(full_path)

    def toggle(self, dirpath):
        full_path = path_join(self.root_dir, dirpath)
        if full_path in self.opened:
            self.opened.remove(full_path)
        else:
            self.opened.add(full_path)
        

    def generated_line(self, curr_dir, filename, flag="f", indent=0):
        if curr_dir:
            full_path = abspath( path_join(self.root_dir, curr_dir, filename) )
            rel_path = full_path[len(self.root_dir)+1:]
        else:
            full_path = abspath( path_join(self.root_dir, filename) )
            rel_path = filename

        icon = ""
        if flag == "d":
            if full_path in self.opened:
                icon = self.dir_opened_icon
            else:
                icon = self.dir_closed_icon
        return {
            "abs": full_path,
            "rel": rel_path,
            "indent": indent,
            "flag": flag,
            "filename": filename,
            "content": (" " * self.indent * indent) + f" {icon} {filename}" 
        }

    def generate(self, curr_dir=None, curr_indent=0):
        dirs = []
        files = []
        dirpath = path_join(self.root_dir, curr_dir) if curr_dir else self.root_dir
        for filename in os.listdir(dirpath):
            if filename[0] == "." and not self.show_hidden:
                continue
            full_path = path_join(dirpath, filename)
            if isdir(full_path):
                dirs.append(filename)
            else:
                files.append(filename)
        dirs.sort()
        for directory in dirs:
            line = self.generated_line(curr_dir, directory, "d", curr_indent)
            yield line
            if line["abs"] in self.opened:
                for subcontent in self.generate(line["rel"], curr_indent+1):
                    yield subcontent 
        files.sort()
        for filename in files:
            yield self.generated_line(curr_dir, filename, "f", curr_indent)

    def show(self):
        for line in self.generate():
            print(line["content"])


class TreeViewer:
    def __init__(self, screen, root_dir, callback):
        self.tree = TreeListing(root_dir)
        self.screen = screen
        self.selected = None
        self.position = 0
        self.data = []
        self.pad = None
        self.callback = callback

    def draw_row(self, rownum, row):
        color = (
            curses.color_pair(1)
            if row["flag"] == "f" else
            curses.color_pair(2)
        )
        if row["rel"] == self.selected:
            self.pad.addstr(rownum, 0, row["content"], color | curses.A_BOLD)
        else:
            self.pad.addstr(rownum, 0, row["content"], color)


    def find_selected(self):
        if not self.selected or self.selected == ".":
            self.selected = None
            return -1
        for rownum, row in enumerate(self.data):
            if row["rel"] == self.selected:
                return rownum
        self.selected = dirname(self.selected)
        return self.find_selected()

    def redraw_selected(self, old_index, new_index):
        height, width = self.screen.getmaxyx()
        if old_index >= 0:
            self.draw_row(old_index, self.data[old_index])
        if new_index >= 0:
            self.draw_row(new_index, self.data[new_index])
        if self.position > new_index:
            self.position = new_index
        if self.position + height-1 < new_index:
            self.position = new_index - height + 1
        self.update_view()

    def move_selected(self, step):
        old_index = self.find_selected()
        index = old_index + step
        if index < 0:
            index = 0
        if index >= len(self.data):
            index = len(self.data)-1
        self.selected = self.data[index]["rel"]
        self.redraw_selected(old_index, index)

    def update_data(self):
        height, width = self.screen.getmaxyx()
        self.data = list(self.tree.generate())
        if self.find_selected() <= 0 and self.data:
            self.selected = self.data[0]["rel"]
        self.pad = curses.newpad(len(self.data), width)
        for rownum, row in enumerate(self.data):
            self.draw_row(rownum, row)
        self.update_view()         
            
    def update_view(self):
        height, width = self.screen.getmaxyx()
        self.screen.clear()
        self.screen.refresh()
        self.pad.refresh(self.position, 0, 0, 0, height-1, width)

    def open(self, directory):
        self.tree.open(directory)
        self.update_data()

    def close(self, directory):
        self.tree.close(directory)
        self.update_data()

    def toggle(self, directory):
        self.tree.toggle(directory)
        self.update_data()
    
    def open_selected(self):
        index = self.find_selected()
        if index >= 0:
            self.open(self.data[index]["rel"])

    def close_selected(self):
        index = self.find_selected()
        if index >= 0:
            self.close(self.data[index]["rel"])

    def default_action(self):
        index = self.find_selected()
        row = self.data[index]
        if row["flag"] == "d":
            return self.toggle(row["rel"])
        return self.callback(row)
        
            

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("cmd", type=str, nargs=REMAINDER)

# ######################################
# callbacks setup
# ######################################

def execute_cmd(params):
    cmd = params.get("cmd")
    def exec_command(row):
        cmd_parsed = []
        for entry in cmd:
            for k,v in row.items():
                entry = entry.replace("{{"+str(k)+"}}", str(v))
            cmd_parsed.append(entry)
        import subprocess
        subprocess.run(cmd_parsed)
    try:
        screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        screen.keypad(True)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)

        viewer = TreeViewer(screen, ".", exec_command)
        viewer.update_data()

        while True:
            kbkey = screen.getkey()
            if kbkey in ("r", "R"):
                viewer.update_data()
            if kbkey == "KEY_DOWN":
                viewer.move_selected(1)
            elif kbkey == "KEY_UP":
                viewer.move_selected(-1)
            elif kbkey == "KEY_RIGHT":
                viewer.open_selected()
            elif kbkey == "KEY_LEFT":
                viewer.close_selected()
            elif kbkey in ("KEY_ENTER", "\n", " "):
                viewer.default_action()
    finally:
        curses.nocbreak()
        screen.keypad(False)
        curses.echo()
        curses.endwin()
	    
