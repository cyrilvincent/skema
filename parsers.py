import bs4
from typing import Dict


class Review:

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.business = None
        self.note = None
        self.nbreview = None
        self.address = None


class MapsParser:

    def __init__(self, html):
        self.html = html
        self.soup = bs4.BeautifulSoup(html, "html.parser")
        self.reviews: Dict[str, Review] = {}
        self.pane: bs4.element.Tag = None

    def soup_pane(self):
        self.pane = self.soup.find("div", attrs={"id": "pane"})
        if self.pane is None:
            print(f"ERROR: soup_pane div pane not found")

    def soup_name(self):
        h1 = self.pane.find("h1")
        span = h1.find("span")
        return str(span.contents[0]).strip().upper()

    def soup_note(self):
        span = self.pane.find("span", attrs={"class", "section-star-display"})
        if span is not None:
            return float(span.contents[0].replace(",", "."))
        return None

    def soup_nbreview(self):
        span = self.pane.find("span", attrs={"class", "reviews-tap-area"})
        if span is not None:
            btn = span.find("button")
            if btn is not None:
                s = str(btn.contents[0])
                return int(s[:-5])
        return None

    def soup_business(self):
        btn = self.pane.find("div", attrs={"jsaction", "pane.rating.category"})
        if btn is not None:
            return str(btn.contents[0]).strip().upper()
        return None

    def soup_address(self):
        return None


