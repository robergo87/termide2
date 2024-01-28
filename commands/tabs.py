# pylint: disable=C0116,C0115,C0114
from os.path import dirname, basename, abspath, isdir, join as path_join
import os, json, subprocess

import curses
from argparse import ArgumentParser, REMAINDER


class TabListing:
    def __init__(self, sid):
        self.tid = None
        self.tabs = []
        self.sid = sid

    def call_space(self, *params):
        return subprocess.check_output(
            ["termide", "space", "--sid", self.sid] 
            + 
            list(params)
        )

    def call_terminals(self):
        return self.call_space("terminals")

    def call_set_terminal(self, tid):
        return self.call_space("terminal-set", "--tid", tid)

    def call_focus(self):
        return self.call_space("focus")

    def generate(self):
        raw_data = self.call_terminals()
        data = json.loads(raw_data)
        self.tid = data.get("current")
        self.tabs = data.get("list", [])
        return self.tabs

    

class TabViewer:
    def __init__(self, screen, sid):
        self.tabs = TabListing(sid)
        self.screen = screen
        self.selected = None
        self.position = 0
        self.data = []
        self.pad = None

    def draw_row(self, rownum, row):
        label = os.path.basename(row)
        if row == self.selected:
            self.pad.addstr(rownum, 0,label, curses.A_BOLD)
        else:
            self.pad.addstr(rownum, 0, label)


    def find_selected(self):
        try:
            return self.data.index(self.selected)
        except ValueError:
            return -1

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
        self.selected = self.data[index]
        self.redraw_selected(old_index, index)
        self.update_view()

    def update_data(self):
        height, width = self.screen.getmaxyx()
        self.data = list(self.tabs.generate())
        if self.find_selected() < 0 and self.data and not self.selected:
            self.selected = self.tabs.tid
        self.pad = curses.newpad(len(self.data), width)
        for rownum, row in enumerate(self.data):
            self.draw_row(rownum, row)
        self.update_view()      
            
    def update_view(self):
        height, width = self.screen.getmaxyx()
        self.screen.clear()
        self.screen.refresh()
        self.pad.refresh(self.position, 0, 0, 0, height-1, width)

    def default_action(self):
        index = self.find_selected()
        row = self.data[index]
        self.tabs.call_set_terminal(row)
        self.tabs.call_set_terminal(row)
        
        
            

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("sid", type=str)

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

        viewer = TabViewer(screen, params.get("sid"))
        viewer.update_data()

        from threading import Thread
        import time
        def refresh():
            while True:
                viewer.update_data()
                time.sleep(1)
		
        t = Thread(target=refresh, daemon=True)
        t.start()
		
        while True:
            kbkey = screen.getkey()
            if kbkey in ("r", "R"):
                viewer.update_data()
            if kbkey == "KEY_DOWN":
                viewer.move_selected(1)
            elif kbkey == "KEY_UP":
                viewer.move_selected(-1)
            elif kbkey in ("KEY_ENTER", "\n", " "):
                viewer.default_action()
    finally:
        curses.nocbreak()
        screen.keypad(False)
        curses.echo()
        curses.endwin()
        
    print(viewer)
