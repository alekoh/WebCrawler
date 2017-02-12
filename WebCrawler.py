from flask import Flask
from flask.ext.mysql import MySQL
from bs4 import BeautifulSoup
import requests
from collections import Counter
import collections
from string import punctuation
from urllib.parse import urldefrag, urljoin, urlparse

app = Flask(__name__)

mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'WebCrawler'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)


def samedomain(netloc1, netloc2):
    """Determine whether two netloc values are the same domain.
    This function does a "subdomain-insensitive" comparison. In other words ...
    samedomain('www.microsoft.com', 'microsoft.com') == True
    samedomain('google.com', 'www.google.com') == True
    samedomain('api.github.com', 'www.github.com') == True
    """
    domain1 = netloc1.lower()
    if '.' in domain1:
        domain1 = domain1.split('.')[-2] + '.' + domain1.split('.')[-1]

    domain2 = netloc2.lower()
    if '.' in domain2:
        domain2 = domain2.split('.')[-2] + '.' + domain2.split('.')[-1]

    return domain1 == domain2


def url_in_list(url, listobj):
    """Determine whether a URL is in a list of URLs.
    This function checks whether the URL is contained in the list with either
    an http:// or https:// prefix. It is used to avoid crawling the same
    page separately as http and https.
    """
    http_version = url.replace('https://', 'http://')
    https_version = url.replace('http://', 'https://')
    return (http_version in listobj) or (https_version in listobj)


def getlinks(pageurl, domain, soup):
    """Returns a list of links from from this page to be crawled.
    pageurl = URL of this page
    domain = domain being crawled (None to return links to *any* domain)
    soup = BeautifulSoup object for this page
    """

    # get target URLs for all links on the page
    links = [a.attrs.get('href') for a in soup.select('a[href]')]

    # remove fragment identifiers
    links = [urldefrag(link)[0] for link in links]

    # remove any empty strings
    links = [link for link in links if link]

    # if it's a relative link, change to absolute
    links = [link if bool(urlparse(link).netloc) else urljoin(pageurl, link)
             for link in links]

    # if only crawing a single domain, remove links to other domains
    if domain:
        links = [link for link in links if samedomain(urlparse(link).netloc, domain)]

    return links


def pagehandler(pageurl, pageresponse, soup):
    """Function to be customized for processing of a single page.
    pageurl = URL of this page
    pageresponse = page content; response object from requests module
    soup = Beautiful Soup object created from pageresponse
    Return value = whether or not this page's links should be crawled.
    """

    print('Crawling:' + pageurl + ' ({0} bytes)'.format(len(pageresponse.text)))

    # take only text elements, count the words and put them into a list -> c
    text = (''.join(s.findAll(text=True)) for s in soup.findAll('p'))
    c = Counter(x.rstrip(punctuation).lower() for y in text for x in y.split())

    # put the words in the database
    conn = mysql.connect()
    cursor = conn.cursor()

    # cursor.callproc('sp_insertPage', pageurl, word, count)

    # print elements as key, value from list c
    for word, counts in [[k, v] for k, v in c.most_common() if len(k) > 3 and v > 3]:
        print(str(pageurl) + ", " + str(word) + ", " + str(counts))
        cursor.callproc('sp_insertPage', (str(pageurl), str(word), counts))
        # print('For page:' + pageurl + ' -> ' + key + ': ' + str(value))
    return True


def crawler(startpage, maxpages=5, singledomain=True):
    """Crawl the web starting from specified page.
        startpage = URL of starting page
        maxpages = maximum number of pages to crawl
        singledomain = whether to only crawl links within startpage's domain
    """

    pagequeue = collections.deque()
    pagequeue.append(startpage)
    crawled = []
    domain = urlparse(startpage).netloc if singledomain else None

    pages = 0  # number of pages succesfully crawled so far
    failed = 0  # number of links that couldn't be crawled

    sess = requests.session()
    while pages < maxpages and pagequeue:
        url = pagequeue.popleft()  # get next page to crawl

        # read the page
        try:
            response = sess.get(url)
        except(requests.exceptions.MissingSchema,
               requests.exceptions.InvalidSchema):
            print("Failed!")
            failed += 1
            continue
        if not response.headers['content-type'].startswith('text/html'):
            continue

        # Parse the HTML using bs4 and lxml for spe1ed
        soup = BeautifulSoup(response.content, "lxml")

        crawled.append(url)
        pages += 1
        if pagehandler(url, response, soup):
            links = getlinks(url, domain, soup)
            for link in links:
                if not url_in_list(link, crawled) and not url_in_list(link, pagequeue):
                    pagequeue.append(link)

crawler("https://pymotw.com/2/collections/counter.html")


@app.route('/')
def hello_world():
    return "Hello World"


if __name__ == '__main__':
    app.run()
