import socket

class URL:
    def __init__(self, url):
        
        # Scheme, url split where scheme = "http"
        self.scheme, url = url.split("://", 1)
        assert self.scheme == "http"
        
        # Host, path split 
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

    # Create a request with sockets
    def request(self):
        s = socket.socket(
            family=socket.AF_INET,      # IPv4
            type=socket.SOCK_STREAM,    # TCP
            proto=socket.IPPROTO_TCP    # TCP protocol
        )

        # Connect on port 80
        s.connect((self.host, 80))

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
