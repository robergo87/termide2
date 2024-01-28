from argparse import ArgumentParser, REMAINDER
from shared.sockets import call_gui
from shared.window import Popup
	

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("cmd", type=str, nargs=REMAINDER)

# ######################################
# callbacks setup
# ######################################

def execute_cmd(params):	
    retval = call_gui("popup", params)

def execute_gui(window, params):
    popup = Popup(pid=window.pid)
    popup.tab.add(command=params["cmd"])
