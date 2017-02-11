from flask import Flask
from bs4 import BeautifulSoup
import requests
from collections import Counter
from string import punctuation


app = Flask(__name__)


# get the web page using requests
r = requests.get("https://www.codementor.io/python/tutorial/python-web-scraping-beautiful-soup")

# Parse the HTML using bs4 and lxml for spe1ed
soup = BeautifulSoup(r.content)

# take only text elements, count the words and put them into a list -> c
text = (''.join(s.findAll(text=True))for s in soup.findAll('p'))
c = Counter(x.rstrip(punctuation).lower()for y in text for x in y.split())

# print elements as key, value from list c
print([[k, v] for k, v in c.most_common() if len(k) > 3])


@app.route('/')
def hello_world():
    return "Hello"


if __name__ == '__main__':
    app.run()
