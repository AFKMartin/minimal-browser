import tkinter as tk
from network import show, URL
import sys

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 20, 20

class Browser:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Minimal Browser")
        self.canvas = tk.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()

    def lex(self, body):
        text = ""
        in_tag = False
        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                text += c
        
        return text

    # load the web
    def load(self, url):
        body = url.request()
        text = self.lex(body)
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in text:
            self.canvas.create_text(cursor_x, cursor_y, text=c)
            cursor_x += HSTEP # advance cursor right after each character

            if cursor_x >= WIDTH - HSTEP:   # near the right edge
                cursor_y += VSTEP           # move down a line
                cursor_x = HSTEP            # reset left margin

if __name__ == "__main__":
    Browser().load(URL(sys.argv[1]))
    tk.mainloop()