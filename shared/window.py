import os, sys, subprocess

import gi
from .terminal import Terminal
from .container import TerminalTab, Container
from shared.sockets import call_gui
from uuid import uuid4

gi.require_version("Gtk", "3.0")
gi.require_version('Keybinder', '3.0')

from gi.repository import Gtk, Gdk, GObject


class GeneralWindow:
    def on_key_press(self, widget, ev, data=None):
        keyset = self.keyset(ev)
        found = False
        for keys, shortcut in self.shortcuts.items():
            if set(keys).difference(keyset):
                continue
            if shortcut[0] == "termide":
                print(self.call_command_sync(shortcut[1:]))
            else:
                subprocess.run(shortcut)
            found = True
        return found    
            
    def on_key_release(self, widget, ev, data=None):
        keyset = self.keyset(ev)
        found = False
        for keys, shortcut in self.shortcuts.items():
            if set(keys).difference(keyset):
                continue
            found = True
        return found    
        
    def call_command_sync(self, argv):
        from importlib import import_module, reload
        command = argv[0]
        try:
            mod = __import__(f"commands.{command}", fromlist=["commands"])
            reload(sys.modules[f"commands.{command}"])
        except ModuleNotFoundError as e:
            return f"Module {command} not found"
        try:
            params = vars(mod.parser.parse_args(argv[1:]))
        except:
            return "Error parsing parameters"
        if hasattr(mod, "execute_gui"):
            return mod.execute_gui(self, params)
        return "Error, execute_gui undefined"        


class Popup(GeneralWindow):
    def __init__(self, pid):
        self.gtkwin = Gtk.Window()
        self.gtkwin.set_default_size(600, 400)
        self.gtkwin.show()
        self.tabs = {}
        self.pid = pid
        self.tab = TerminalTab(window=self, parent=self, position=0, uid="ROOT")
        self.gtkwin.add(self.tab)
        self.tab.show()
        self.gtkwin.set_focus(self.tab)
    
    def split(self, num, vertical, uid=None, *args, **kwargs):
        pass    

    def close(self, tid):
        self.gtkwin.close()
                
    def move(self, x, y):
        pass

    def set_width(self, num, value, absolute):    
        pass

    def set_height(self, num, value, absolute):    
        pass
        
    def set_child(self, num, child):
        self.remove(self.tab)
        self.add(child)
        self.root = child
        self.root.show()

    def on_focus(self, uid):
        self.tab.set_focus(True)                 



class Window(GeneralWindow):
    def __init__(self):
        self.gtkwin = Gtk.Window()
        self.gtkwin.connect("destroy", Gtk.main_quit)
        self.gtkwin.show()
        self.gtkwin.maximize()
        
        self.box = Gtk.Frame()
        self.gtkwin.add(self.box)
        self.box.show()
        
        self.pid = os.getpid()
        self.tabs = {}        
        
        tab = TerminalTab(window=self, parent=self, position=0, uid="ROOT")
        self.box.add(tab)
        tab.show()
        tab.add()
        tab.set_focus(True)

        self.current = tab
        self.root = tab
        
        self.gtkwin.connect("key-press-event", self.on_key_press)   
        self.gtkwin.connect("key-release-event", self.on_key_release)   
        
        self.shortcuts = {}
        #self.keys_pressed = set()
        
    def shortcut_set(self, keybinding, argv):
        keys = keybinding.split("+")
        keys.sort()
        keys = tuple (keys)
        if keys in self.shortcuts:
            return False
        self.shortcuts[keys] = argv
        return True

    def keyset(self, event):
        keyname = Gdk.keyval_name(event.keyval)
        keys_pressed = set([keyname])
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            keys_pressed.add("Control")
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            keys_pressed.add("Shift")
        if event.state & Gdk.ModifierType.MOD1_MASK:
            keys_pressed.add("Alt")
        return keys_pressed
    
    def call_idle(self, callback):
        GObject.idle_add(callback)
        
    def on_focus(self, uid):
        self.focus_tab(uid)
    
    def focus_tab(self, uid):
        self.current = self.tabs[uid]
        for tid, tab in self.tabs.items():
            tab.set_focus(uid==tid)                 
            
    def split(self, num, vertical, uid=None, directory=None, *args, **kwargs):
        self.box.remove(self.root)
        split = Container(
            window = self, parent=self, 
            vertical=vertical, position=0
        )
        self.box.add(split)
        split.show()

        split.set_child(0, self.root)
        self.root.position = 0
        self.root.parent = split

        terminal = TerminalTab(
            window=self, parent=split, position=1, uid=uid, *args, **kwargs
        )
        split.set_child(1, terminal)
        terminal.show()        
        terminal.add(directory=directory, *args, **kwargs)
        if self.current:    
            self.current.set_focus(True)
        self.root = split    

    def close(self, tid):
        pass
                
    def move(self, x, y):
        curr_coords = self.current.translate_coordinates(
            self.box, 
            self.current.get_allocated_width() * (0.5 + x/2), 
            self.current.get_allocated_height() * (0.5 + y/2) 
        )
        new_tab_uid = self.current.uid
        new_tab_score = (
            self.box.get_allocated_width()
            +
            self.box.get_allocated_height()
        )
        for tid, tab in self.tabs.items():
            if tid == self.current.uid:
                continue
            coords = tab.translate_coordinates(
                self.gtkwin,
                tab.get_allocated_width() * (0.5 - x/2), 
                tab.get_allocated_height() * (0.5 - y/2) 
            )
            if (coords[0] - curr_coords[0]) * x < 0:
                continue
            if (coords[1] - curr_coords[1]) * y < 0:
                continue
            score = (
                abs(curr_coords[0] - coords[0])
                +
                abs(curr_coords[1] - coords[1])
            )
            if score >= new_tab_score:
                continue
            new_tab_score = score
            new_tab_uid = tid
        if new_tab_uid == self.current.uid:
            return False
        self.focus_tab(new_tab_uid)
        return new_tab_uid

    def set_width(self, num, value, absolute):    
        pass

    def set_height(self, num, value, absolute):    
        pass
        
    def set_child(self, num, child):
        self.box.remove(self.root)
        self.box.add(child)
        self.root = child
        self.root.show()

    def run(self):
        self.root.feed(" termide macro run GLOBAL\n")
        Gtk.main()        
        
    
"""    
    def terminal_show(self, container_id, terminal_id):
        if container_id not in self.containers:
            return None, None
        container = self.containers[container_id]
        if terminal_id not in self.containers[container_id]["terminals"]:
            return container_id, None
        for termid, terminal in self.containers[container_id]["terminals"].items():
            if termid == terminal_id:
                terminal["node"].show()
            else:
                terminal["node"].hide()
        return container_id, terminal_id        
    
    def terminal_add(self, container_id, font=None, commands=None):
        terminal_id = uuid4().hex
        terminal = Terminal()
        if container_id not in self.containers:
            return None
        container = self.containers[container_id]
        terminal.embed(
            self, container_id, terminal_id, 
            container["w"], container["h"]
        )
        self.containers[container_id]["terminals"][terminal_id] = {
            "node": terminal,
            "font": font if font else container["font"],
            "commands": commands if commands else container["commands"]
        }
        container["node"].add(terminal)
        self.terminal_show(container_id, terminal_id)
        return terminal_id
        
    def container_add(self, x, y, label="", w=None, h=None, font=12, command=None):
        container = Terminal
        if not w:
            w = Terminal().get_char_width() * 80
        if not h:
            h = Terminal().get_char_height() * 20
        container_id = uuid4().hex
        container = TerminalTab(self, label="Label")
        self.box.put(container, x, y)
        container.set_size_request(w, h)
        self.containers[container_id] = {
            "node": container,
            "terminals": {},
            "x": x, "y": y, "w": w, "h": h, 
            "font": font, "commands": commands
        }
        self.terminal_add(container_id, font, commands)
        return container_id
"""
        


