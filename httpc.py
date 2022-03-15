import socket
import argparse
import sys
from urllib.parse import urlparse

#######################################HELP MESSAGES##################################################
help_get = """httpc help get
usage: httpc get [-v] [-h key:value] URL
Get executes a HTTP GET request for a given URL.
	-v Prints the detail of the response such as protocol, status, and headers.
	-h key:value Associates headers to HTTP Request with the format 'key:value'."""

help_post = """httpc help post
usage: httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL
Post executes a HTTP POST request for a given URL with inline data or from file.
	-v		Prints the detail of the response such as protocol, status, and headers.
	-h key:value	Associates headers to HTTP Request with the format 'key:value'.
	-d string	Associates an inline data to the body HTTP POST request.
	-f file		Associates the content of a file to the body HTTP POST request.
	Either [-d] or [-f] can be used but not both."""

general_help = """httpc help
httpc is a curl-like application but supports HTTP protocol only.
Usage:
	httpc command [arguments]
The commands are:
	get	executes a HTTP GET request and prints the response.
	post	executes a HTTP POST request and prints the response.
	help	prints this screen.

Use "httpc help [command]" for more information about a command."""
#####################################################################################################

##################################HELPER METHODS#####################################################
def strip_http_headers(http_reply):
    p = http_reply.find('\r\n\r\n')
    if p >= 0:
        return http_reply[p+4:]
    return http_reply

def check_for_dupplicates(args_list):
	args_counter = {}
	for element in args_list:
		if element not in args_counter:
			args_counter[element] = 1
		else:
			args_counter[element] += 1
	
	if "-v" in args_counter and args_counter["-v"] >= 2:
		return "Please provide only one -v"
	elif "-d" in args_counter and args_counter["-d"] >= 2:
		return "Please provide only one -d"
	elif "-f" in args_counter and args_counter["-f"] >= 2:
		return "Please provide only one -f"

	return None

def get_redirect_path(response):
    response_list = response.split()	#splits on whitespaces
    index = response_list.index("location:")	#get index of location: because next index is the redirect path
    redirect_path = response_list[index + 1]
    return redirect_path

#####################################################################################################

def get_request(verbose, headers, output_file, url, port, request="GET"):
	host = urlparse(url).netloc
	all_headers = "\r\n".join(headers)
	request_get = f'{request} {url} HTTP/1.0\r\nHost: {host}\r\n{all_headers}\r\n\r\n'
	full_response = do_request(verbose, host, port, request_get, output_file, request)

	redirect_url = do_redirect(host, full_response)
	if (redirect_url):
		get_request(verbose, headers, output_file, redirect_url, port, request)

def post_request(verbose, headers, body, file, output_file, url, port, request="POST"):
	host = urlparse(url).netloc

	if file:
		with open(file, "r") as file:
			body = file.read()

	all_headers = "\r\n".join(headers)
	if headers:
		request_post = f"POST {url} HTTP/1.0\r\nHost: {host}\r\nContent-Length: {str(len(body))}\r\n{all_headers}\r\n\r\n{body}\r\n"
	else:
		request_post = f"POST {url} HTTP/1.0\r\nHost: {host}\r\nContent-Length: {str(len(body))}\r\n\r\n{body}\r\n"
	full_response = do_request(verbose, host, port, request_post, output_file, request)
	
	redirect_url = do_redirect(host, full_response)
	if (redirect_url):
		post_request(verbose, headers, body, file, output_file, redirect_url, port, request)

def do_request(verbose, host, port, request_string, output_file, request):
	mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	mysock.connect((host.split(f":{port}")[0], port))
	cmd = request_string.encode()
	mysock.send(cmd)

	response = ''
	while True:
		data = mysock.recv(512)
		response += data.decode()
		if (len(data) < 1):
			break
	
	full_response = response
	if (not verbose):
		response = strip_http_headers(full_response)

	if(output_file):
		with open(output_file, "w") as file:
			file.write(response)
	else:
		print(response)

	mysock.close()

	return full_response

def do_redirect(host, response):
	status_code = int(response.split()[1])
	if status_code == 302:
		redirect_path = get_redirect_path(response)
		redirect_url = "http://"+host+redirect_path
		print(f"Redirect URL: {redirect_url}")
		follow = input("Do you wish to follow this redirect URL (yes or no)?\n")
		if follow == "yes":
			return redirect_url
		else:
			return False

def main():
	commandline_args = sys.argv[1:]
	num_commandline_args = len(commandline_args)

	error = check_for_dupplicates(commandline_args)
	if error:
		print(f"Syntax Error: {error}")
		return

	if len(commandline_args) < 1:
		print("Command Line arguments are missing! Please run 'httpc help' for detailed usage")
		return

	if (commandline_args[0] == 'help'):
		if (num_commandline_args >= 2 and commandline_args[1] == 'get'):
			print(help_get)
		elif (num_commandline_args >= 2 and commandline_args[1] == 'post'):
			print(help_post)
		else:
			print(general_help)
		return

	parser = argparse.ArgumentParser(add_help=False, usage='httpc (get|post) [-v] (-h "k:v")* [-d inline-data] [-f file] URL [-o output-file]')
	parser.add_argument("request", help="request", choices=["get", "post"])
	parser.add_argument("-v", help="Prints the status, headers and contents of the response.", default=False, required=False, action="store_true")
	parser.add_argument("-h", metavar='"k:v"', help="setting the header of the request in the format 'key: value.' you can have multiple headers by having the -h option before each header parameter.", default=[], required=False, action="append")
	parser.add_argument("url", help="url")
	action = parser.add_mutually_exclusive_group(required=False)
	action.add_argument("-d", metavar="inline-data", help="Associate the body of the HTTP Request with the inline data", required=False)
	action.add_argument("-f", metavar="file", help="Associate the body of the HTTP Request with the data from a given file", required=False)
	parser.add_argument("-o", metavar="output file", help="Write the body of the response to the specified file instead of the console", required=False)
	args = parser.parse_args()

	url = args.url
	port = 9080		#UPDATE THIS BASED ON SERVER
	request = args.request.upper()
	if request == "GET":
		if args.d or args.f:
			parser.error("get request should not be used with the options -d or -f.")
		get_request(args.v, args.h, args.o, url, port, request)
	elif request == "POST":
		if not (args.d or args.f):
			parser.error("post request should be used with the options -d or -f (but not both).")
		post_request(args.v, args.h, args.d, args.f, args.o, url, port, request)

if __name__ == "__main__":
    main()