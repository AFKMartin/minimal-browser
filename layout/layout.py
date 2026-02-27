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
        self.size = 12

        if self.rtl:
            self.cursor_x = self.width - HSTEP
            self.cursor_y = VSTEP
            for tok in tokens:
                if isinstance(tok, Text):
                    continue
                for c in tok.text:
                    if c == "\n":
                        self.cursor_y += VSTEP * 2
                        self.cursor_x = self.width - HSTEP
                        continue
                    
                    self.display_list.append((self.cursor_x, self.cursor_y, c, self.font))
                    self.cursor_x -= HSTEP

                    if self.cursor_x < HSTEP:
                        self.cursor_y += VSTEP
                        self.cursor_x = self.width - HSTEP
        
        else:
            self.cursor_x = HSTEP
            self.cursor_y = VSTEP
            for tok in tokens:
                self.token(tok)
    
    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4

    def word(self, word):
        font = tkf.Font(
            size=self.size,
            weight=self.weight,
            slant=self.style,
        )
        w = font.measure(word)
        
        if self.cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH:
            self.cursor_y += font.metrics("linespace") * 1.25
            self.cursor_x = HSTEP
        
        self.display_list.append((self.cursor_x, self.cursor_y, word, font))
        self.cursor_x += w + font.measure(" ")
