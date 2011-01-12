## {{{ http://code.activestate.com/recipes/576832/ (r2)
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, mm

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont('Times-Roman', 10)
        self.drawRightString(200 * mm, 0.25 * inch,
            "Page %d/%d" % (self._pageNumber, page_count))
