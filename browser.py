import tkinter as tk
from network import show, URL
import sys
import os
import tkinter.font as tkf
from parsing.html_parser import lex, Text, Tag
from layout.layout import Layout
from constants import WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP, SCROLLBAR_WIDTH, EMOJI_SIZE, OPENMOJI_DIR

def is_emoji(c):
    if len(c) != 1:
        return False
    else:
        cp = ord(c)
        return (
            0x1F300 <= cp <= 0x1FAFF or # Misc symbols, emoticons, transport, etc.
            0x2600  <= cp <= 0x27BF or  # Misc symbols, dingbats
            0x2300  <= cp <= 0x23FF     # Misc technical
        )

class Browser:
    def __init__(self, rtl=False):
        self.rtl = rtl # text direction flag
        self.emoji_cache = {}

        self.window = tk.Tk()
        self.window.title("Minimal Browser")
        self.canvas = tk.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            bg="white"
        )
        
        # fil and expand
        self.canvas.pack(fill="both", expand=True) 
        self.scroll = 0
        self.width = WIDTH
        self.height = HEIGHT
        self.max_scroll = 0

        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.on_mousewheel)
        # Linux scroll events, b4 and b5 intead of mousewheel
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        # Bind winddow resize
        self.window.bind("<Configure>", self.on_resize)        
        # fonts
        self.font = tkf.Font()

    # emoji
    def get_emoji_image(self, c):
        # return a cached 16x16 emoji character c, or None
        if c in self.emoji_cache:
            return self.emoji_cache[c]
        codepoint = format(ord(c), "X")
        path = os.path.join(OPENMOJI_DIR, f"{codepoint}.png")
        img = None
        if os.path.exists(path):
            try:
                raw = tk.PhotoImage(file=path)
                # subsample to 16×16 
                factor = raw.width() // EMOJI_SIZE
                img = raw.subsample(factor, factor) if factor > 1 else raw
            except Exception:
                img = None
        self.emoji_cache[c] = img   # cache even on failure so we dont retry
        return img        

    def load(self, url):
        # handle about:blank
        try:
            if isinstance(url, str) and url == "about:blank":
                self.tokens = []
            else:
                body = url.request()
                self.tokens = lex(body)
        except Exception:
            self.tokens = []
            
        self.display_list = Layout(self.tokens, self.width, self.rtl, self.font).display_list
        self._update_max_scroll()
        self.draw()

    def draw(self):
        self.canvas.delete("all") # Delete old text when scrolling
        for x, y, c, font in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + font.metrics("linespace") < self.scroll:
                continue
            screen_y = y - self.scroll

            if len(c) == 1 and is_emoji(c):
                img = self.get_emoji_image(c)
                if img:
                    self.canvas.create_image(x, screen_y, image=img, anchor="nw")
                    continue

            self.canvas.create_text(x, screen_y, text=c, font=font, anchor="nw")

        self._draw_scrollbar()
        
    def _draw_scrollbar(self):
        
        total = self.max_scroll + self.height
        if total <= self.height:
            return

        bar_height = max(20, self.height * self.height / total)
        bar_top    = self.scroll * (self.height - bar_height) / self.max_scroll if self.max_scroll else 0

        x0 = self.width - SCROLLBAR_WIDTH
        self.canvas.create_rectangle(
            x0, bar_top,
            self.width, bar_top + bar_height,
            fill="blue", outline=""
        )

    def _update_max_scroll(self):

        if self.display_list:
            last_y = max(y for _, y, _, _ in self.display_list)
            last_font = self.display_list[-1][3]
            line_height = last_font.metrics("linespace") * 1.25
            self.max_scroll = max(0, last_y - self.height + line_height * 2)
        else:
            self.max_scroll = 0

    def scrolldown(self, e):
        self.scroll = min(self.max_scroll, self.scroll + SCROLL_STEP)
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
            if hasattr(self, "tokens"):
                self.display_list = Layout(self.tokens, self.width, self.rtl, self.font).display_list
                self._update_max_scroll()
                self.scroll = min(self.scroll, self.max_scroll)
            self.draw()

if __name__ == "__main__":
    rtl = "--rtl" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        raw = args[0]
        # about:black or any exeption falls back to a blank page
        if raw == "about:blank":
            url = "about:blank"
        else:
            try:
                url = URL(raw)
            except Exception:
                url = "about:blank"
    else:
        url = "about:blank"
    
    Browser(rtl=rtl).load(url)
    tk.mainloop()