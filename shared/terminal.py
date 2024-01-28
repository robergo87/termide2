import os
from os.path import dirname, abspath
import gi
from uuid import uuid4

gi.require_version("Gtk", "3.0")
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Vte, Gdk 
from gi.repository import GLib, GObject

class Terminal(Vte.Terminal):
    def __init__(self, window, parent, directory=None, command=None, uid=None):
        super().__init__()

        self.uid = uid if uid else uuid4().hex
        self.window = window
        self.parent = parent
        self.directory = directory if directory else os.getcwd()
        self.command = command if command else self.command_bash()
        #self.set_size(800, 200)
        
        self.set_color_background(Gdk.RGBA(0.16, 0.18, 0.20, 1))
        self.set_clear_background(True)
        _, self.terminal_pid = self.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            self.directory, self.command,
            [
                f"TERMIDE_PID={self.window.pid}", 
                self.pathvar(),
            ],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None, None,
        )
        self.connect("focus_in_event", self.on_focus)
        self.connect("eof", self.on_eof)

    def on_eof(self, event):
        self.parent.terminal_close(self.uid)

    def __repr__(self):
        return f"Terminal {self.uid} {self.directory} {self.command}"
    
    def on_focus(self, *args, **kwargs):
        self.parent.on_focus(self.uid)

    def pathvar(self):
        ROOT_DIR = dirname(dirname(abspath(__file__)))
        return "PATH={}".format(
            os.environ["PATH"] + os.pathsep + ROOT_DIR)
    
    def command_bash(self):
        return ["/bin/bash"]
            
    def getcwd(self):
        return os.readlink(f'/proc/{self.terminal_pid}/cwd')
        


"""
class Terminal(Vte.Terminal):
    default_dir = os.getcwd()
    
    def __init__(self, title, directory=None, commands = []):
        super().__init__()
        self.title = title
        self.set_color_background(Gdk.RGBA(0.2, 0.2, 0.2, 1))
        self.set_clear_background(False)
        self.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            directory if directory else self.default_dir,
            commands if commands else bash(), 
            [
                "TERMIDE_PIPE_PATH={}".format(PIPE_PATH),
                "PATH={}".format(os.environ["PATH"] + os.pathsep + os.path.join(ROOT_DIR, "script"))
            ],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None, None,
        )
        self.connect("eof", self.event_eof)
        self.connect("focus_in_event", self.event_focus)
        self.termno = -1
        self.tid = None
        self.add_tick_callback(self.tick_cb)
        
    def event_eof(self, event):
        print("eof caught");
        self.prnt.rem_terminal(self.termno)

    def event_focus(self, *args):
        self.prnt.tab_focused()

    def getcwd(self):
        return self.default_dir
        try:
            return "/"+"/".join(self.get_current_directory_uri().split("/")[3:])
        except Exception as e:
            print("Exception path")
            print(e)
            return None

    def tick_cb(self, *args):
        self.prnt.tick_cb()
 """
