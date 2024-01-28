import socket
import os, sys
import threading
import ctypes
import json
import traceback
from signal import pthread_kill, SIGTSTP
# Set the path for the Unix socket


def call_command(argv, pid):
	if not argv:
		return False
	command = argv[0]
	from importlib import import_module, reload
	try:
		mod = __import__(f"commands.{command}", fromlist=["commands"])
		reload(sys.modules[f"commands.{command}"])
	except ModuleNotFoundError as e:
		cb(f"Module {command} not found")
		return False
	try:
		params = vars(mod.parser.parse_args(argv[1:]))
	except:
		cb(f"Error parsing parameters")
		return False
	print("Calling gui", command, params)
	print(call_gui(command, params, pid))
		

def call_gui(command, params, pid=None):
	if not pid:
		pid = os.environ.get("TERMIDE_PID", 0)
	if not pid:
		return False
	payload = {
		"command": command,
		"params": params
	}
	return json.dumps(call_single(pid, payload))

def call_single(pid, content):
	socket_path = f"/tmp/termide-{pid}"
	if not os.path.exists(socket_path):
		return None
	client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	client.connect(socket_path)
	try:	
		client.send(json.dumps(content).encode())
		raw = client.recv(10240).decode()
		return json.loads(raw)
	finally:
		client.close()				


class Client:
	def __init__(self, pid):
		self.pid = pid
		self.socket_path = f"/tmp/termide-{pid}"
		
	
		
class ServerThread(threading.Thread):
	def stop(self):
		pthread_kill(self.ident, SIGTSTP)
                        
		
class Server:

	def __init__(self, pid):
		self.pid = pid
		self.socket_path = f"/tmp/termide-{pid}"
		self.running = False
		self.handler = None
		try:
			os.unlink(self.socket_path)
		except OSError:
			if os.path.exists(self.socket_path):
				raise
				
		self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	
	def handle(self, handler, scope=None):
		self.handler = handler
		self.scope = scope
		
	def run(self, parallel=False):
		self.socket.bind(self.socket_path)
		self.socket.listen(1)

		self.running = True
		try:
			while self.running:
				connection, client_address = self.socket.accept()
				args = (connection, client_address)
				if parallel:
					threading.Thread(target=self.run_connection, args=args)
				else:	
					self.run_connection(*args)
		finally:
			os.unlink(self.socket_path)
			self.running = False
			print("Exited")
	
	def run_threaded(self, parallel=False):
		thread = ServerThread(target=self.run, args=(parallel,))
		thread.start()
		return thread

	def run_connection(self, connection, client_address):
		try:
			while True:
				if not self.handler:
					break
				try:
					data = connection.recv(1024)
				except:
					break
				if not data:
					break
				data = json.loads(data.decode())
				def cb(connection, response):
					connection.sendall(json.dumps(response).encode())
				simple = self.handler(data, self.scope, cb, connection)	
				if simple:
					break
		finally:
			connection.close()		


if __name__ == "__main__":
	import sys
	if sys.argv[1] == "server":
		server = Server(1)
		def handler(data, scope):
			print(data)
			return data, True
		server.handle(handler, {})
		server.run()
	if sys.argv[1] == "client":
		output = call_single(1, {"message": sys.argv[2]})
		print(output)
		
	
