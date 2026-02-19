import tkinter as tk
from network import show, URL
import sys

WIDTH, HEIGHT = 800, 600

class Browser:
    def __init__(self):
        self.window = tk.Tk()
        self.canvas = tk.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
   
    # load the web
    def load(self, url):
        body = url.request()
        # Handle view-source
        if url.scheme == "view-source":
            print(body)
        else:
            show(body)
        # Test stuff
        self.canvas.create_rectangle(10, 20, 400, 300)
        self.canvas.create_oval(100, 100, 150, 150)
        self.canvas.create_text(200, 150, text="Test")


if __name__ == "__main__":
    Browser().load(URL(sys.argv[1]))
    tk.mainloop()