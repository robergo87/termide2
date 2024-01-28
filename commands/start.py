import sys
from importlib import reload
from argparse import ArgumentParser
parser = ArgumentParser()


def handle_calls(data, window, cb, connection):
	from importlib import import_module
	command = data.get("command", "help")
	params = data.get("params", {})
	try:
		mod = __import__(f"commands.{command}", fromlist=["commands"])
		reload(sys.modules[f"commands.{command}"])
	except ModuleNotFoundError as e:
		cb(f"Module {command} not found")
		return True
	if hasattr(mod, "execute_gui"):
		try:
			def call_gui():
				response = mod.execute_gui(window, params)
				cb(connection, response)
				connection.close()
				return False
			window.call_idle(call_gui)
			return False
		except Exception as e:
			cb(str(e))
			print(e)
			traceback._exc()
			return True
	cb(f"Module {command} not callable by GUI")
	return f"Module {command} not callable by GUI", True
	

def execute_cmd(params):
	from shared.window import Window
	from shared.sockets import Server
	
	win = Window()
	server = Server(win.pid)
	server.handle(handle_calls, win)
	thread = server.run_threaded()

	win.run()
	thread.stop()


