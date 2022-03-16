import argparse
import os
import socket
import threading

from time import gmtime, strftime

def start_server(verbose, port, dir):
	print("Server is starting...")
	HOST = "localhost"
	ADDR = (HOST, port)
	print("(Host, Port): ", ADDR)
	
	if dir is None:
		dir = os.path.dirname(os.path.realpath(__file__))
	print("DIRECTORY: ", dir)
	
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind(ADDR)
	server.listen()
	print("Server is running\n")
	while True:
		conn, addr = server.accept()
		threading.Thread(target = handle_client_request,args=(conn, addr, port, dir, verbose)).start()

def handle_client_request(conn, addr, port, dir, verbose):
	print(f"[NEW CONNECTION] {addr} connected.")
	verbose_msg = ""
	try:
		data = conn.recv(1024)
		data = data.decode('utf-8')

		# Parse the request from client 
		request_content = data.split("\r\n\r\n")
		header_contents = request_content[0].split()
		request_method = header_contents[0]
		verbose_msg += f"REQUEST METHOD: {request_method}\n"
		request_path = header_contents[1].split(f"{port}/")[1]
		if not request_path:
			request_path = "/"
		verbose_msg += f"REQUEST PATH: {request_path}\n"
		
		request_body = None
		if len(request_content)>1: 
			request_body = request_content[1]
			verbose_msg += f"REQUEST BODY: {request_body}\n"
		
		###################### Do GET or POST ######################
		response_body = ""
		status_line = "HTTP/1.0 "
		files = os.listdir(dir)
		verbose_msg += f"CONTENT OF DIRECTORY: {files}\n"

		#bad request if client tries to go to parent directory
		if ".." in request_path:
			status_line += "403 Forbidden \r\n"
			verbose_msg += "[ERROR 403] Forbidden access outside of working directory\n"

		elif request_method == "GET":
			if request_path == "/":
				for file in files:
					response_body += file + "\n"
				status_line += "200 OK \r\n"
				verbose_msg += "[SUCCESS] Files in working directory were retrieved\n"
			else:
				try:
					with open(dir+"/"+request_path, "r") as file:
						file_content = file.read()
					response_body = file_content
					status_line += "200 OK \r\n"
					verbose_msg += "[SUCCESS] File content was retrieved\n"
				except EnvironmentError:
					status_line += "404 Not Found \r\n"
				if not response_body:
					verbose_msg += "[ERROR 404] File not found in working directory\n"

		elif request_method == "POST" and request_body != None:
			try:
				with open(dir+"/"+request_path, "w") as file:
					file.write(request_body)
				status_line += "200 OK \r\n"
				verbose_msg += "[SUCCESS] File content was updated\n"
			except EnvironmentError:
				status_line += "404 Not Found \r\n"
				verbose_msg += "[ERROR 404] File not found in working directory\n"
		else:
			status_line += "400 Bad Request \r\n"
			verbose_msg += "[ERROR 400] Bad Request\n"
		
		# Send Response Message back to client
		response_headers = "Date: " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " GMT\r\n"
		response_headers += "Connection: close\r\n"

		response_headers += "Server: httpfs \r\nAccept-Ranges: bytes \r\n"
		body_length = len(response_body)

		content_headers = "Content-Type: text \r\nContent-Length: " + str(body_length) + "\r\n\r\n"
		response = status_line + response_headers + content_headers + response_body

		conn.sendall(response.encode('utf-8'))
		if verbose:
			print(verbose_msg)
	finally:
		print(f"[CLOSE CONNECTION] {addr} closed.\n")
		conn.close()


parser = argparse.ArgumentParser(description="httpfs is a simple file server.", usage="httpfs [-v] [-p PORT] [-d PATH-TO-DIR]")
parser.add_argument("-v", help="Prints debugging messages.", default=False, required=False, action="store_true")
parser.add_argument("-p", metavar="port", help="Specifies the port number that the server will listen and serve at. Default is 8080.", default=8080, type=int, required=False)
parser.add_argument("-d", metavar="path-to-dir", help="Specifies the directory that the server will use to read/write requested files. Default is the current directory when launching the application.", default=os.getcwd(), required=False)
args = parser.parse_args()
start_server(args.v, args.p,args.d)