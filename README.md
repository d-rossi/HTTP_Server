# HTTP_Server

Command-line application to send HTTP requests.

David Rossi 40095896

**Run**
---
1. Start the server. Optionally, specify the port number using the -p argument and the path of the working directory using the -d argument.

`python httpfs.py -v -p 9080`

2. Change the port number in the httpc.py (line 167) to match the port of the server.

`port = 9080`

3. Test the server using the http client

- Get files in current directory: `python httpc.py get -v "http://localhost:9080/"`
- Get file content: `python httpc.py get -v "http://localhost:9080/test.txt"`
- Get file content inside subdirectory: `python httpc.py get -v "http://localhost:9080/foo/bar.txt"`
- Try to get file content from a file in parent directory: `python httpc.py get -v "http://localhost:9080/../test.txt"`
- File not found: `python httpc.py get -v "http://localhost:9080/foo"`
- Update file content: `python httpc.py post -v "http://localhost:9080/test.txt" -d "Hello world"`
- Create a new file with content from an existing file: `python httpc.py post -v -f test.txt "http://localhost:9080/foo/doc.txt"`
