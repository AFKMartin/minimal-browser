import tkinter as tk
from network import show, URL
import sys

WIDTH, HEIGHT = 1200, 800
HSTEP, VSTEP = 20, 20
SCROLL_STEP = 100

class Browser:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Minimal Browser")
        self.canvas = tk.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        # fil and expand
        self.canvas.pack(fill="both", expand=True) 
        self.scroll = 0
        self.width = WIDTH
        self.height = HEIGHT
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.on_mousewheel)
        # Linux scroll events, b4 and b5 intead of mousewheel
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        # Bind winddow resize
        self.window.bind("<Configure>", self.on_resize)        

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

    def load(self, url):
        body = url.request()
        text = self.lex(body)
        self.text = text # store text so we can relayout
        self.display_list = self.layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all") # Delete old text when scrolling
        for x, y, c in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=("Noto Sans CJK", 12))
        
    def layout(self, text):
        display_list = []
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in text:
            # handle newline
            if c == "\n":
                cursor_y += VSTEP * 2
                cursor_x = HSTEP
                continue
            
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP

            if cursor_x >= self.width - HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP

        return display_list

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()
    
    def scrollup(self, e):
        self.scroll = max(0, self.scroll - SCROLL_STEP)
        self.draw()
    
    def on_mousewheel(self, e):
        if e.delta > 0:
            self.scrollup(e)
        else:
            self.scrolldown(e)

    def on_resize(self, e):
        # update stored dimensions and redo layout whenever the window changes
        if e.widget is self.window:
            self.width = e.width
            self.height = e.height
            if hasattr(self, "text"):
                self.display_list = self.layout(self.text)
            self.draw()

if __name__ == "__main__":
    Browser().load(URL(sys.argv[1]))
    tk.mainloop()