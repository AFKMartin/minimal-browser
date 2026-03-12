import tkinter.font as tkf
import tkinter as tk
from constants import HSTEP, VSTEP, SCROLLBAR_WIDTH
from parsing.html_parser import Text, Tag

FONTS = {}
SOFT_HYPHEN = "\N{soft hyphen}"

def get_font(size, weight, style, family=None):
    key = (size, weight, style, family)
    if key not in FONTS:
        kwargs = dict(size=size,
                      weight=weight,
                      slant=style)
        if family:
            kwargs["family"] = family
        font = tkf.Font(**kwargs)
        label = tk.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

class Layout:
    def __init__(self, tokens, width, rtl, font):
        self.display_list = []
        self.weight = "normal"
        self.style = "roman"
        self.width = width
        self.rtl = rtl
        self.font = font
        self.size = 12
        self.line = []
        self.centered = False
        self.superscript = False
        self.abbr = False
        self.pre = False

        if self.rtl:
            self.cursor_x = self.width - HSTEP
            self.cursor_y = VSTEP * 2
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
            self.flush()
    
    def token(self, tok):
        if isinstance(tok, Text):
            if self.pre:
                self.pre_text(tok.text)
            elif self.abbr:
                for word in tok.text.split():
                    self.abbr_word(word)
            else:
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
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
        elif tok.tag == 'h1 class="title"':
            self.flush()
            self.centered = True
        elif tok.tag == "/h1":
            self.flush()
            self.centered = False
        elif tok.tag == "sup":
            self.superscript = True
            self.size = max(1, self.size // 2)
        elif tok.tag == "/sup":
            self.superscript = False
            self.size *= 2
        elif tok.tag == "abbr":
            self.abbr = True
        elif tok.tag == "/abbr":
            self.abbr = False
        elif tok.tag == "pre":
            self.flush()
            self.pre = True
        elif tok.tag == "/pre":
            self.flush()
            self.pre = False

    def word(self, word):
        if SOFT_HYPHEN in word:
            self.word_with_soft_hyphens(word)
            return
        
        font = get_font(
            size=self.size,
            weight=self.weight,
            style=self.style,
        )
        w = font.measure(word)
        
        if self.cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH:
            self.flush()
        
        self.line.append((self.cursor_x, word, font, self.superscript))
        self.cursor_x += w + font.measure(" ")
    
    def word_with_soft_hyphens(self, word):
        parts = word.split(SOFT_HYPHEN)
        font = get_font(self.size,
                        self.weight,
                        self.style)
        
        current = ""
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            candidate = current + part
            suffix = "" if is_last else "-"
            w = font.measure(candidate + suffix)

            if self.cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH and current:
                # render current + hyphen, the start new line
                display = current + "-"
                self.line.append((self.cursor_x, display, font, self.superscript))
                self.cursor_x += font.measure(display)
                self.flush()
                current = part
            else:
                current = candidate
        if current:
            w = font.measure(current)
            if self.cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH:
                self.flush()
            self.line.append((self.cursor_x, current, font, self.superscript))
            self.cursor_x += w + font.measure(" ")
    
    def abbr_word(self, word):
        i = 0
        while i < len(word):
            c = word[i]
            if c.islower():
                j = i
                while j < len(word) and word[j].islower():
                    j += 1
                sub = word[i:j].upper()
                font = get_font(max(1, self.size - 2), "bold", self.style)
                w = font.measure(sub)
                if self.cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH:
                    self.flush()
                self.line.append((self.cursor_x, sub, font, self.superscript))
                self.cursor_x += w
                i = j
            else:
                j = i
                while j < len(word) and not word[j].islower():
                    j += 1
                sub = word[i:j]
                font = get_font(self.size, self.weight, self.style)
                w = font.measure(sub)
                if self.cursor_x + w > self.width - HSTEP - SCROLLBAR_WIDTH:
                    self.flush()
                self.line.append((self.cursor_x, sub, font, self.superscript))
                self.cursor_x += w
                i = j
        
        font = get_font(self.size, self.weight, self.style)
        self.cursor_x += font.measure(" ")
    
    def pre_text(self, text):
        lines = text.split("\n")
        for i, line_text in enumerate(lines):
            if i > 0:
                self.flush()
            parts = line_text.split(" ")
            for j, part in enumerate(parts):
                font = get_font(self.size, self.weight, self.style, family="Courier New")
                if part:
                    self.line.append((self.cursor_x, part, font, False))
                    self.cursor_x += font.measure(part)
                if j < len(parts) - 1:
                    self.cursor_x += font.measure(" ")

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font, sup in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        if self.centered:
            line_width = self.cursor_x - HSTEP
            content_width = self.width - 2 * HSTEP - SCROLLBAR_WIDTH
            offset = max(0, (content_width - line_width) / 2)
        else:
            offset = 0
        
        for x, word, font, sup in self.line:

            if sup:
                y =  baseline - max_ascent
            else:
                y = baseline - font.metrics("ascent")
            self.display_list.append((x + offset, y, word, font))

        max_descent = max([metric["descent"] for metric in metrics])

        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []

