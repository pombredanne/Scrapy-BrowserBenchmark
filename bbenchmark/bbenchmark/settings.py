# Scrapy settings for bbenchmark project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'bbenchmark'

SPIDER_MODULES = ['bbenchmark.spiders']
NEWSPIDER_MODULE = 'bbenchmark.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'bbenchmark (+http://www.yourdomain.com)'

DOWNLOADER_HTTPCLIENTFACTORY = 'warcclientfactory.WarcHTTPClientFactory'

# Use priority 820 to capture the data before Scrapy modifies it
DOWNLOADER_MIDDLEWARES = {'warcmiddleware.WebkitDownloader': 820}

