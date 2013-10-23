import urlparse
from cStringIO import StringIO

import scrapy.http
import twisted.web.http
from scrapy.utils.httpobj import urlparse_cached

import warcrecords

from scrapy.http import HtmlResponse

import gtk
import webkit
import jswebkit
import gzip
import StringIO

# from scrapy/core/downloader/webclient.py
def _parsed_url_args(parsed):
    path = urlparse.urlunparse(('', '', parsed.path or '/', parsed.params,
                                parsed.query, ''))
    host = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme
    netloc = parsed.netloc
    if port is None:
        port = 443 if scheme == 'https' else 80
    return scheme, netloc, host, port, path

class WarcMiddleware(object):
    """
    Open the WARC file for output and write the warcinfo header record
    
    """
    def __init__(self):
        self.fo = open('out.warc', 'wb')
        record = warcrecords.WarcinfoRecord()
        record.write_to(self.fo)

    """
    Converts a Scrapy request to a WarcRequestRecord
    Follows most of the code from scrapy/core/downloader/webclient.py
    
    """
    def warcrec_from_scrapy_request(self, request):
        headers = request.headers
        body = request.body

        parsed = urlparse_cached(request)
        scheme, netloc, host, port, path = _parsed_url_args(parsed)

        headers.setdefault('Host', netloc)

        if body is not None and len(body) > 0:
            headers['Content-Length'] = len(body)
            headers.setdefault("Connection", "close")

        # Compile the request using buf
        buf = StringIO()
        buf.write('%s %s HTTP/1.0\r\n' % (request.method, path))
        for name, values in headers.items():
            for value in values:
                buf.write('%s: %s\r\n' % (name, value))
        buf.write('\r\n')
        if body is not None:
            buf.write(body)
        request_str = buf.getvalue()
        
        return warcrecords.WarcRequestRecord(url=request.url, block=request_str)


    def decode(self, page):
        data = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(page))
        page = data.read()

        return page

    """
    Converts a Scrapy response to a WarcResponseRecord
    
    tofix: Handle response.status codes
    
    """
    def warcrec_from_scrapy_response(self, response):
        # Everything is OK.
        resp_str = "HTTP/1.0 " + str(response.status) + " OK\r\n"
        resp_str += response.headers.to_string()
        resp_str += "\r\n\r\n"
        encoding = response.headers.get("Content-Encoding")    
        if encoding in ('gzip', 'x-gzip', 'deflate'):
            resp_str += self.decode(response.body)
        else:
            resp_str += response.body

        return warcrecords.WarcResponseRecord(url=response.url, block=resp_str)

    def process_request(self, request, spider):
        record = self.warcrec_from_scrapy_request(request)
        record.write_to(self.fo)

    def process_response(self, request, response, spider):
        record = self.warcrec_from_scrapy_response(response)
        record.write_to(self.fo)
        return response # return the response to Scrapy for further handling

class WebkitDownloader( WarcMiddleware ):
	
    def stop_gtk(self, v, f):
        gtk.main_quit()

    def reload_page_yq(self, v, f):
        self.webview.connect('load-finished', self.stop_gtk)
        ctx = jswebkit.JSContext(self.webview.get_main_frame().get_global_context())
        ctx.EvaluateScript('''a = function __inserted__() { 
							var anchors = document.getElementsByTagName('a'); 
								for (var i = 0; i < anchors.length; ++i) 
								 { 
									if (anchors[i].innerText === 'Graphics HTML5 Canvas') {
									 anchors[i].click(); 
									 break; 
								} 
							}
							return 0;
						}''')
 
    def _get_webview(self):
        self.webview = webkit.WebView()
        props = self.webview.get_settings()
        props.set_property('enable-java-applet', False)
        props.set_property('enable-plugins', False)
        props.set_property('enable-page-cache', False)

    def process_request( self, request, spider ):
        if 'triggerjs' in request.meta:
            self._get_webview()
            self.webview.connect('load-finished', self.reload_page_yq)
            self.webview.load_uri(request.url)
            gtk.main()
            ctx = jswebkit.JSContext(self.webview.get_main_frame().get_global_context())
            url = ctx.EvaluateScript('window.location.href')
            html = ctx.EvaluateScript('document.documentElement.innerHTML')
            return HtmlResponse(url, encoding='utf-8', body=html.encode('utf-8'))

        if 'renderjs' in request.meta:
            self._get_webview()
            self.webview.connect('load-finished', self.stop_gtk)
            self.webview.load_uri(request.url)
            gtk.main()
            ctx = jswebkit.JSContext(self.webview.get_main_frame().get_global_context())
            url = ctx.EvaluateScript('window.location.href')
            html = ctx.EvaluateScript('document.documentElement.innerHTML')
            return HtmlResponse(url, encoding='utf-8', body=html.encode('utf-8'))

