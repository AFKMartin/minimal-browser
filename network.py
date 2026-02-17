import socket
import sys
import ssl
import os

DEFAULT_FILE = os.path.abspath("test.html")

class URL:
    def __init__(self, url):
        # Handle view-source
        if url.startswith("view-source:"):
            self.scheme = "view-source"
            self.inner = URL(url[len("view-source:"):])
            return
        
        # Handle data
        if url.startswith("data:"):
            self.scheme = "data"
            _, rest = url.split(":", 1)
            self.mimetype, self.data = rest.split(",", 1)
            self.host = self.port = self.path = None
            return
        
        # Scheme, url split where scheme = "http"
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]
        
        # file URLs
        if self.scheme == "file":
            self.path = url
            self.host = self.port = None
            return 
            
        # Host, path split 
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        # Parse port from host if present
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

        else:
            # If HTTP use port 80 if HTTPS user port 443
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443

    # Create a request with sockets
    def request(self):
        # Handle view-source
        if self.scheme == "view-source":
            return self.inner.request()
        
        # Handle data
        if self.scheme == "data":
            return self.data
        
        # file URLs
        if self.scheme == "file":
            with open(self.path, "r", encoding="utf8") as f:
                return f.read()
        
        s = socket.socket(
            family=socket.AF_INET,      # IPv4
            type=socket.SOCK_STREAM,    # TCP
            proto=socket.IPPROTO_TCP    # TCP protocol
        )

        # Connect to port and wrap socket
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # Default headers
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "Minimal-Web-Browser/1.0",
        }

        # HTTP/1.1 request
        request = "GET {} HTTP/1.1\r\n".format(self.path)   # Request line with the path
        for header, value in headers.items():               
            request += "{}: {}\r\n".format(header, value)
        request += "\r\n"                                   # End of header (blank line)

        s.send(request.encode("utf8"))                      # Send the request as UTF-8

        # Wrap the socket as a text stream for easy reading
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # split the response
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        # Read all HTTP headers into a dictionary 
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        # Ensure simple response format (no chunking or compression)
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        # Return content and close connection
        content = response.read()
        s.close()

        return content
    
def show(body):
    in_tag = False
    i = 0
    while i < len(body):
        c = body[i]
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            # Check entities
            if body[i:i+4] == "&lt;":
                print("<", end="")
                i+=4
                continue
            elif body[i:i+4] == "&gt;": 
                print(">", end="")
                i+=4
                continue
            else:
                print(c, end="")
        i+=1

# load the web
def load(url):
    body = url.request()
    # Handle view-source
    if url.scheme == "view-source":
        print(body)
    else:
        show(body)
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        load(URL(sys.argv[1]))
    else:
        load(URL("file://" + DEFAULT_FILE))


