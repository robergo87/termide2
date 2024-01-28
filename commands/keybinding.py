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
	
@register("set")
def kb_set(window, params):
	args = params.get("args", [])
	print(args)
	window.shortcut_set(args[0], args[1:])	

@register("del")
def kb_del(window, params):
	args = params.get("args", [])
	window.shortcut_del(args[0])	

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("action", type=str, choices=list(commands.keys()))
parser.add_argument("args", type=str, nargs=REMAINDER)

# ######################################
# callbacks setup
# ######################################

def execute_cmd(params):	
	retval = call_gui("keybinding", params)
	if retval and retval != "null":
		sys.stdout.write(str(retval)+"\n")

def execute_gui(window, params):
	return commands[params.get("action")](window, params)

