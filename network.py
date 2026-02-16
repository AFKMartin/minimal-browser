import socket
import sys
import ssl

class URL:
    def __init__(self, url):
        
        # Scheme, url split where scheme = "http"
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]
        
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

        # Raw HTTP request
        request = "GET {} HTTP/1.0\r\n".format(self.path)   # Request line with the path
        request += "Host: {}\r\n".format(self.host)         # Required host header
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
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")

# load the web
def load(url):
    body = url.request()
    show(body)
    
if __name__ == "__main__":
    load(URL(sys.argv[1]))


