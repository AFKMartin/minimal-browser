import tkinter as tk
from network import show, URL
import sys
import os
import tkinter.font as tkf

WIDTH, HEIGHT = 1200, 800
HSTEP, VSTEP = 20, 20
SCROLL_STEP = 100
SCROLLBAR_WIDTH = 12
EMOJI_SIZE = 16
OPENMOJI_DIR = "openmoji" # folder for emojis read README for more info.

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
        # handle about:blank
        try:
            if isinstance(url, str) and url == "about:blank":
                self.text = ""
            else:
                body = url.request()
                self.text = self.lex(body)
        except Exception:
            self.text = ""
            
        self.display_list = self.layout(self.text)
        self._update_max_scroll()
        self.draw()

    def draw(self):
        self.canvas.delete("all") # Delete old text when scrolling
        for x, y, c in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + self.font.metrics("linespace") < self.scroll:
                continue
            screen_y = y - self.scroll

            if len(c) == 1 and is_emoji(c):
                img = self.get_emoji_image(c)
                if img:
                    self.canvas.create_image(x, screen_y, image=img, anchor="nw")
                    continue

            self.canvas.create_text(x, screen_y, text=c, font=("Noto Sans CJK", 12))

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
            last_y = max(y for _, y, _ in self.display_list)
            line_height = self.font.metrics("linespace") * 1.25
            self.max_scroll = max(0, last_y - self.height + line_height * 2)
        else:
            self.max_scroll = 0

    def layout(self, text):
        # font = tkf.Font() # may cause problems
        display_list = []
        
        if self.rtl:         
            cursor_x = self.width - HSTEP
            cursor_y = VSTEP
            for c in text:
                # handle newline
                if c == "\n":
                    cursor_y += VSTEP * 2
                    cursor_x = self.width - HSTEP
                    continue
                
                display_list.append((cursor_x, cursor_y, c))
                cursor_x -= HSTEP

                if cursor_x < HSTEP:
                    cursor_y += VSTEP
                    cursor_x = self.width - HSTEP
        
        else:
            cursor_x, cursor_y = HSTEP, VSTEP
            for word in text.split():
                w = self.font.measure(word)

                if cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH:
                    cursor_y += self.font.metrics("linespace") * 1.25
                    cursor_x = HSTEP
                
                display_list.append((cursor_x, cursor_y, word))
                cursor_x += w + self.font.measure(" ")

        return display_list

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
            if hasattr(self, "text"):
                self.display_list = self.layout(self.text)
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