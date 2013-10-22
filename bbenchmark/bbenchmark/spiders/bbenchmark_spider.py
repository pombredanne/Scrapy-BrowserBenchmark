from scrapy.spider import BaseSpider

class BBenchmarkSpider(BaseSpider):
    name = "bbench"
    allowed_domains = ["browsermark.rightware.com"]
    start_urls = [
        "http://browsermark.rightware.com/"
    ]

    def parse(self, response):
        filename = response.url.split("/")[-2]
        open(filename, 'wb').write(response.body)
