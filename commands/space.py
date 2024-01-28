import sys

from argparse import ArgumentParser, REMAINDER
from shared.sockets import call_gui


# ######################################
# helper decorator
# ######################################

commands = {}
def register(*labels):
    def inner(cb):
        for label in labels:
            commands[label] = cb
        return cb
    return inner

# ######################################
# command definitions
# ######################################
    
@register("vsplit", "vs")
def command_vsplit(window, params):
    nid = params.get("nid")
    if nid:
        window.current.split(1, uid=nid)        
    else:
        window.current.split(1)
    
@register("hsplit", "hs")
def command_hsplit(window, params):    
    nid = params.get("nid")
    if nid:
        window.current.split(0, uid=nid)        
    else:
        window.current.split(0)

@register("close", "x")
def command_close(window, params):
    window.current.close()

@register("left", "lt")
def command_left(window, params):
    print("LT", window.move(-1, 0))

@register("right", "rt")
def command_right(window, params):    
    window.move(+1, 0)

@register("up")
def command_top(window, params):    
    window.move(0, -1)

@register("down", "dn")
def command_bottom(window, params):    
    window.move(0, +1)

@register("width_rel", "wr")
def command_bottom(window, params):
    size = params.get("size")
    print("params", params)
    window.current.set_width(size, absolute=False)

@register("width_abs", "wa")
def command_bottom(window, params):
    size = params.get("size")
    window.current.set_width(size, absolute=True)

@register("height_abs", "ha")
def command_bottom(window, params):
    size = params.get("size")
    window.current.set_height(size, absolute=True)


@register("focus")
def command_focus(window, params):
    window.focus_tab(window.current.uid)

@register("reopen")
def command_reopen(window, params):
    tid = params.get("tid")
    
    window.current.reopen(tid, command=params.get("cmd"))

@register("feed")
def command_feed(window, params):
    print("CURR", window.current.uid)
    cmd = [entry if entry != "<Enter>" else "\n" for entry in params.get("cmd")]
    window.current.feed("".join(cmd) )

@register("copy")
def command_copy(window, params):
    window.current.clipboard_copy()

@register("paste")
def command_paste(window, params):
    window.current.clipboard_paste()


@register("terminals")
def terminal_list(window, params):
    return {
        "current": window.current.current().uid,
        "list": list(window.current.terminals)
    }

@register("terminal_close")
def terminal_close(window, params):
    space = window.current
    tid = params.get("tid")
    if not tid:
        tid = space.current().uid
    space.terminal_close(tid)

@register("terminal-set")
def terminal_set(window, params):
    space = window.current
    tid = params.get("tid", space.current().uid)
    space.switch(tid)    

@register("terminal-first")
def terminal_first(window, params):
    space = window.current
    space.switch(space.terminal_list[0])

@register("terminal-last")
def terminal_lasr(window, params):
    space = window.current
    space.switch(space.terminal_list[-1])

@register("terminal_prev")
def terminal_prev(window, params):
    space = window.current
    tid = params.get("tid")
    if not tid:
        tid = space.current().uid
    index = space.terminal_list.index(tid) - 1
    if index >= 0:
        space.switch(space.terminal_list[index])

@register("terminal_next")
def terminal_next(window, params):
    space = window.current
    tid = params.get("tid")
    if not tid:
        tid = space.current().uid
    index = space.terminal_list.index(tid) + 1
    if index < len(space.terminal_list):
        space.switch(space.terminal_list[index])



# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("action", type=str, choices=list(commands.keys()))
parser.add_argument("--size",type=int, nargs="?", default=400)
parser.add_argument("--tid", type=str)
parser.add_argument("--sid", type=str)
parser.add_argument("--nid", type=str)
parser.add_argument("--cmd", type=str, nargs="*")
parser.add_argument("--focus", type=int, default=0)


# ######################################
# callbacks setup
# ######################################

def execute_cmd(params):    
    retval = call_gui("space", params)
    if retval and retval != "null":
        sys.stdout.write(str(retval)+"\n")

def execute_gui_new(window, params):
    sid = params.get("sid")
    tab = window.current
    if sid and sid in window.tabs:
        window.current = window.tabs[sid]
    try:
        return commands[params.get("action")](window, params)
    finally:
        if params.get("action") == "move":
	        return 
        if params.get("focus"):
            window.focus_tab(sid)
        else:
            window.current = tab
        
def execute_gui(window, params):
    sid = params.get("sid")
    focus = params.get("focus")
    action = params.get("action")
    tab = window.current.uid
    if sid not in window.tabs:
        sid = None
    if sid:
        window.focus_tab(sid)
    try:
        return commands[action](window, params)
    finally:
        if sid and not focus:
            window.focus_tab(tab)
            


