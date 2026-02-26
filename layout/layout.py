import tkinter.font as tkf
from constants import HSTEP, VSTEP, SCROLLBAR_WIDTH
from parsing.html_parser import Text, Tag

class Layout:
    def __init__(self, tokens, width, rtl, font):
        self.display_list = []
        self.weight = "normal"
        self.style = "roman"
        self.width = width
        self.rtl = rtl
        self.font = font

        if self.rtl:
            cursor_x = self.width - HSTEP
            cursor_y = VSTEP
            for tok in tokens:
                if isinstance(tok, Text):
                    continue
                for c in tok.text:
                    if c == "\n":
                        cursor_y += VSTEP * 2
                        cursor_x = self.width - HSTEP
                        continue
                    
                    self.display_list.append((cursor_x, cursor_y, c, self.font))
                    cursor_x -= HSTEP

                    if cursor_x < HSTEP:
                        cursor_y += VSTEP
                        cursor_x = self.width - HSTEP
        
        else:
            cursor_x, cursor_y = HSTEP, VSTEP
            for tok in tokens:
                if isinstance(tok, Text):
                    for word in tok.text.split():
                        font = tkf.Font(
                            size=16,
                            weight=self.weight,
                            slant=self.style,
                        )
                        w = font.measure(word)

                        if cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH:
                            cursor_y += font.metrics("linespace") * 1.25
                            cursor_x = HSTEP
                        
                        self.display_list.append((cursor_x, cursor_y, word, font))
                        cursor_x += w + font.measure(" ")
                
                elif tok.tag == "i":
                    self.style = "italic"
                elif tok.tag == "/i":
                    self.style = "roman"
                elif tok.tag == "b":
                    self.weight = "bold"
                elif tok.tag == "/b":
                    self.weight = "normal"

