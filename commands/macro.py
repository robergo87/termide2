import subprocess
import os
from os.path import dirname, abspath, join as join_path

from argparse import ArgumentParser
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
	
ROOT_DIR = abspath(dirname(dirname(__file__)))
	
def pathvar():
	return os.environ["PATH"] + os.pathsep + ROOT_DIR
			
@register("run")
def run_macro(params, pid=None):
	name = params.get("name")
	if not pid:
		pid=os.environ.get("TERMIDE_PID")
	path = join_path(ROOT_DIR, "macro", f"{name}.sh")
	env = dict(os.environ)
	env.update({
		"TERMIDE_PID": str(pid),
		"PATH": pathvar()
	})
	subprocess.run(["bash", path], env=env) 
	

# ######################################
# argparse setup
# ######################################

parser = ArgumentParser()
parser.add_argument("action", type=str)
parser.add_argument("name", type=str)

# ######################################
# callbacks setup
# ######################################

def execute_cmd(params):	
	return commands[params.get("action")](params)

def execute_gui(window, params):
	print("Exec macro", params)
	return commands[params.get("action")](params)

