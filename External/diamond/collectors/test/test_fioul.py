import requests
import logging
import lxml.html as LH


class Test:
    def __init__(self):
        self.log = logging

    def text(self, elt):
        return elt.text_content().replace(u'\xa0', u' ')

    def get_fioul_price(self, url):
        price = -1.0

        r = requests.get(url)
        root = LH.fromstring(r.content)

        for th in root.xpath('//div[@id="tableau1"]/div/table/thead/tr/th'):
            if u'FIOUL\nORDINAIRE' in self.text(th):
                break
        else:
            self.log.error("Fioul page has change (1): update script.")

        tds = root.xpath('//div[@id="tableau1"]/div/table/tbody/tr/td')
        for idx, td in enumerate(tds):
            if u"1 000 à 1 999 litres" in self.text(td):
                price_ht = float(self.text(tds[idx + 1]).replace(',', '.'))
                price = price_ht * 1.20
                break
        else:
            self.log.error("Fioul page has change (2): update script.")

        return price

if __name__ == "__main__":
    Test().get_fioul_price("https://www.eleclerc-serviceouest.com/nos-tarifs/")
       