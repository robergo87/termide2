import os
import gi
from uuid import uuid4

gi.require_version("Gtk", "3.0")
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Vte, Gdk 

from .terminal import Terminal


class TerminalTab(Gtk.Box):
    def __init__(self, window, parent, position, font=None, uid=None, directory=None):
        super().__init__(spacing=6)

        self.window = window
        self.parent = parent
        self.position = position
        self.uid = uid if uid else uuid4().hex
        self.font = font if font else 1
        self.terminals = {}
        self.terminal_list = []
        self.set_hexpand(True)
        
        self.frame = Gtk.Frame()
        self.frame.set_border_width(1)
        self.frame.set_hexpand(True)
        super().add(self.frame)
        self.frame.show()
        
        self.stack = Gtk.Stack()
        self.frame.add(self.stack)
        self.stack.show()
        
        self.window.tabs[self.uid] = self
            
    def on_focus(self, uid):
        self.window.on_focus(self.uid)
            
    def current(self):
        return self.stack.get_visible_child()

    def set_focus(self, state):
        color = (
            Gdk.RGBA(0.15, 0.17, 0.19, 1) 
            if state else
            Gdk.RGBA(0.16, 0.18, 0.20, 1) 
        )
        for tid, terminal in self.terminals.items():
            terminal.set_color_background(color)
        if state:
            self.current().grab_focus()
            self.window.current = self


    def feed(self, text):
        self.current().feed_child(str(text).encode())

    def clipboard_copy(self):
        self.current().copy_clipboard()

    def clipboard_paste(self):
        self.current().paste_clipboard()

        
    def list(self):
        return list(self.terminals.keys())    
        
    def switch(self, terminal_id):
        if terminal_id in self.terminals:
            self.stack.set_visible_child(self.terminals[terminal_id])
            return True
        return False

    def terminal_close(self, terminal_id):
        if terminal_id not in self.terminals:
            return False
        index = self.terminal_list.index(terminal_id)
        index = max(0, index-1)
        self.terminal_list.remove(terminal_id)
        terminal = self.terminals[terminal_id]
        self.stack.remove(terminal)
        del self.terminals[terminal_id]
        if not self.terminals:
            self.parent.close(self.position)
        else:
            self.stack.set_visible_child(self.terminal_list[index])
    
        
    def reopen(self, uid, directory=None, command=None):
        if uid not in self.terminals:
            self.add(directory, command, uid)
        print("terminals", self.terminals)
        return self.switch(uid)
            
        
    def add(self, directory=None, command=None, uid=None):
        if not directory and self.current():
            directory = self.current().getcwd()
        terminal = Terminal(
            window=self.window, 
            parent=self, 
            directory=directory, 
            command=command,
            uid=uid
        )
        self.stack.add(terminal)
        terminal.show()
        self.terminals[terminal.uid] = terminal
        self.terminal_list.append(terminal.uid)
        self.switch(terminal.uid)
        return terminal.uid
        
    def get(self, terminal_id):
        if terminal_id not in self.terminals:
            return None
        return self.terminals[terminal_id]
        
    def split(self, vertical, uid=None, directory=None, *args, **kwargs):
        if not directory and self.current():
            directory = self.current().getcwd()
        print("split dir", directory, self.current().getcwd())
        return self.parent.split(
            num=self.position, vertical=vertical, uid=uid, 
            directory=directory, *args, **kwargs
        )
    
    def move_x(self, change):
        #self.window.move_x(self.uid, change)
        pass
        
    def move_y(self, change):
        #self.window.move_y(self.uid, change)
        pass
    
    def set_width(self, value, absolute=True):
        self.parent.set_width(self.position, value, absolute)
    
    def set_height(self, value, absolute=True):
        self.parent.set_height(self.position, value, absolute)
        
    def close(self):
        return self.parent.close(num=self.position)
        
    def first_tab_uid(self):
        return self.uid

    def get_child_tabs(self):
        return [self]
        
class Container(Gtk.Paned):
    def __init__(self, window, parent, position, vertical=True):
        orientation = (
            Gtk.Orientation.VERTICAL
            if vertical else
            Gtk.Orientation.HORIZONTAL
            
        )
        super().__init__(orientation=orientation)
        self.set_wide_handle(True)
        self.window = window
        self.parent = parent
        self.position = position
        self.uid = uuid4().hex
        self.vertical = vertical

    def first_tab_uid(self):
        return self.get_child(0).first_tab_uid()
                            
    def set_width(self, num, value, absolute):
        if self.vertical:
            return self.parent.set_width(self.position, value, absolute)
        if num and self.parent.set_width(self.position, value, absolute):
            return True
        if not absolute:
            position = self.get_position()
            self.set_position(position - value)
            return True
        position = self.get_allocated_width() - value if num else value
        self.set_position(position)
        return True
            
    def set_height(self, num, value, absolute):            
        if not self.vertical:
            return self.parent.set_height(self.position, value, absolute)
        if num and self.parent.set_height(self.position, value, absolute):
            return True
        if not absolute:
            position = self.get_position()
            self.set_position(position - value)
            return True
        position = self.get_allocated_height() - value if num else value
        self.set_position(position)
        return True
                        
                
    def get_child(self, num):
        if num:
            return self.get_child2()
        else:
            return self.get_child1()

    def set_child(self, num, child):
        current = self.get_child(num)
        if current:
            self.remove(current)
        if num:
            self.pack2(child, True, True)
        else:
            self.pack1(child, True, True)

    def get_child_tabs(self):
        return self.get_child(0).get_child_tabs()+self.get_child(1).get_child_tabs()
            
    def close(self, num):
        remaining_num = 0 if num else 1
        remaining = self.get_child(remaining_num)
        for closing_tab in self.get_child(num).get_child_tabs():
            del self.window.tabs[closing_tab.uid]
        self.remove(remaining)
        remaining.position = self.position
        self.parent.set_child(self.position, remaining)
        remaining.parent = self.parent
        self.window.focus_tab(remaining.first_tab_uid())
        
    def split(self, num, vertical, uid=None, directory=None, *args, **kwargs):
        last_focus_tab = self.window.current.uid
        position = self.get_position()
        current = self.get_child(num)
        self.remove(current)

        split = Container(
            window = self.window, parent=self, 
            vertical=vertical, position=num
        )
        self.set_child(num, split)
        split.show()

        split.set_child(0, current)
        current.position = 0
        current.parent = split

        terminal = TerminalTab(window=self.window, parent=split, position=1, uid=uid)
        split.set_child(1, terminal)
        terminal.show()        
        terminal.add(directory=directory, *args, **kwargs)
        
        self.set_position(position)
        self.window.focus_tab(last_focus_tab)
    
    
    
    
    
    

        


