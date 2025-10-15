class Document:
    def __init__(self, multiline_text: str):
        lines: list["Line"] = []
        for linenum, text in enumerate(multiline_text.split("\n")):
            text = text.strip()
            if len(text) > 0:
                lines.append(Line(self, linenum, text))

        self.lines = lines
        print(f"Loaded document with {len(lines)} lines")

    @staticmethod
    def from_file(path: str):
        with open(path, "rt") as f:
            return Document(f.read())

    def as_paragraph(self) -> "Paragraph":
        return Paragraph(self, 0, len(self.lines))

class Line:
    def __init__(self, doc: Document, linenum: int, text: str):
        assert "\n" not in text
        self.doc = doc
        self.linenum = linenum
        self.text = text

    def __str__(self) -> str:
        return self.text

class Paragraph:
    def __init__(self, doc: Document, start_idx: int, end_idx: int):
        assert start_idx < end_idx

        assert 0 <= start_idx
        assert end_idx <= len(doc.lines)

        self.doc = doc
        self.sidx = start_idx
        self.eidx = end_idx

    @property
    def position(self) -> str:
        return f"{self.sidx}-{self.eidx}"

    @property
    def num_lines(self) -> int:
        return self.eidx - self.sidx

    @property
    def lines(self) -> list[Line]:
        return self.doc.lines[self.sidx : self.eidx]

    def as_multiline_text(self) -> str:
        result = ""

        cur_linenum: int | None = None
        for line in self.lines:
            if cur_linenum is None:
                cur_linenum = line.linenum
            else:
                assert cur_linenum < line.linenum

            while cur_linenum < line.linenum:
                cur_linenum += 1
                result += "\n"
            result += line.text
        return result

    def split(self, new_sz: int) -> list["Paragraph"]:
        start_idx = self.sidx

        res: list["Paragraph"] = []
        while start_idx < self.eidx:
            end_idx = start_idx + new_sz

            done = self.eidx <= end_idx
            if done:
                end_idx = self.eidx
            res.append(Paragraph(self.doc, start_idx, end_idx))
            if done:
                break
            else:
                start_idx += new_sz

        return res

if __name__ == "__main__":
    doc = Document(
        """qwerty

asdfg
zxcvbb
fdsafds

fdsaf
ds

f
a
sdf
sfafs
a"""
    )

    pars = doc.as_paragraph().split(3)

    for par in pars:
        print("---")
        print(par.as_multiline_text())
