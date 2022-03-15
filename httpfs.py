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



parser = argparse.ArgumentParser(description="httpfs is a simple file server.", usage="httpfs [-v] [-p PORT] [-d PATH-TO-DIR]")
parser.add_argument("-v", help="Prints debugging messages.", default=False, required=False, action="store_true")
parser.add_argument("-p", metavar="port", help="Specifies the port number that the server will listen and serve at. Default is 8080.", default=8080, type=int, required=False)
parser.add_argument("-d", metavar="path-to-dir", help="Specifies the directory that the server will use to read/write requested files. Default is the current directory when launching the application.", default=os.getcwd(), required=False)
args = parser.parse_args()
start_server(args.v, args.p,args.d)