# pylint: disable=C0116,C0115,C0114

import curses
from threading import Thread
import time


class Listing:
    def __init__(self, interval=1):
        self.screen = None
        self.selected = None
        self.position = 0
        self.data = []
        self.pad = None
        self.interval = interval
        self.keybindings = {}
        self.background_thread = None
        self.running = False

    def draw_row(self, rownum, row):
        height, width = self.screen.getmaxyx()
        selected = rownum == self.find_selected()
        if selected:
            def printfunc(content, flags = 0):
                if len(content) > width-1:
                    content = content[0:width-4]+"..."
                self.pad.addstr(rownum, 0, content, flags | curses.A_BOLD)
        else:
            def printfunc(content, flags = 0):
                if len(content) > width:
                    content = content[0:width-2]+".."
                self.pad.addstr(rownum, 0, content, flags)
        self.draw_single_row(row, selected, printfunc)

    def redraw_selected(self, old_index, new_index):
        height, _ = self.screen.getmaxyx()
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
        if old_index < 0:
            index = 0 if step >= 0 else len(self.data)-1
        else:
            index = old_index + step
        if index < 0:
            index = 0
        if index >= len(self.data):
            index = len(self.data)-1
        self.selected = self.row_key(self.data[index])
        self.redraw_selected(old_index, index)
        self.update_view()

    def update_data(self):
        _, width = self.screen.getmaxyx()
        self.data = self.generate()
        self.pad = curses.newpad(len(self.data), width)
        for rownum, row in enumerate(self.data):
            self.draw_row(rownum, row)
        self.update_view()

    def update_view(self):
        height, width = self.screen.getmaxyx()
        #self.screen.clear()
        self.screen.refresh()
        self.pad.refresh(self.position, 0, 0, 0, height-1, width-1)
        last_line = len(self.data) - self.position
        for rownum in range(last_line, height):
            self.screen.addstr(rownum, 0, " "*(width-1))

        
    def keybinding(self, keylist, unbind=False):
        if unbind:
            for keyname in keylist:
                del self.keybindings[keyname]
            return None
        def inner(callback):
            for keyname in keylist:
                self.keybindings[keyname] = callback
            return callback
        return inner

    def default_keybindings(self):
        @self.keybinding(["r", "R"])
        def callback(listing):
            listing.update_data()

        @self.keybinding(["KEY_DOWN"])
        def callback(listing):
            listing.move_selected(1)

        @self.keybinding(["KEY_UP"])
        def callback(listing):
            listing.move_selected(-1)
            
        @self.keybinding(["KEY_ENTER", "\n"])
        def callback(listing):
            listing.default_action()

    def refresh(self):
        while True:
            self.update_data()
            time.sleep(self.interval)

    def run_refresh_thread(self):
        self.background_thread = Thread(target=self.refresh, daemon=True)
        self.background_thread.start()

    def init_curses(self):
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)

    def close_curses(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()
    
    def run(self, refresh_thread=True, default_keybindings=True):
        try:
            self.init_curses()
            self.update_data()
            
            if refresh_thread:
                self.run_refresh_thread()		
            if default_keybindings:
                self.default_keybindings()

            self.running = True
            while self.running:
                kbkey = self.screen.getkey()
                if kbkey == "KEY_RESIZE":
                    self.update_view()
                if kbkey in self.keybindings:
                    self.keybindings[kbkey](self)
        finally:
            self.close_curses()

    def find_selected(self):
        for index, row in enumerate(self.data):
            if self.row_key(row) == self.selected:
                return index
        return -1


    def default_action(self):
        raise NotImplementedError()

    def generate(self):
        raise NotImplementedError()
        #return []

    def draw_single_row(self, row, is_selected, printfunc):
        raise NotImplementedError()      

    def row_key(self, row):
        return row
        
