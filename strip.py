from pprint import pprint
from collections import namedtuple
from functools import partial
import pickle

import pypandoc
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import bs4

BASE_URL = "https://www.legal-alien.ru"
#CONTENT_URL = "almanakh/akuly-iz-stali"
CONTENT_URL = "/memuaristika/gornokopytnye-slegka-bronirovannye/rukha"


Item = namedtuple('Item', 'url name depth childrens content')


def valid_ref(ref, processed):
    if (ref['href'] in processed
            or ref.text.strip() in ('Тудак', 'Судак')):
        return False
    return True

def get_soup(url):
    url = BASE_URL+url
    raw_html = requests.get(url).content.decode('utf8')
    soup = BeautifulSoup(raw_html, 'lxml')
    return soup


def get_table_of_content(url, processed=None, depth=1, table_of_content=None, name=''):
    if table_of_content is None:
        table_of_content = dict()
    if processed is None:
        processed = set()
    processed.add(url)
    soup = get_soup(url)
    refs = [ref for ref in soup.find_all(name='a', href=True)
            if ref['href'].startswith(CONTENT_URL)]
    validref = partial(valid_ref, processed=processed)
    refs = filter(validref, refs)

    childrens = []
    for ref in refs:
        print((depth-1)*'\t' + ref.text.strip())
        childrens.append(get_table_of_content(ref['href'],
                                              processed,
                                              depth+1,
                                              table_of_content,
                                              ref.text.strip()))
    item = Item(
        url=url,
        depth=depth,
        name=name,
        childrens=childrens,
        content=strip_fragment(soup)
        )
    return item


def strip_fragment(soup):
    content = soup.find(name='div', attrs={'itemprop': 'articleBody'})
    if content is None:
        print('content is None')
        return soup.new_tag('div')
    tags = content.find_all()
    # TODO fix condition
    for tag in tags:
        if tag.name is None or tag.name in ('a', 'i', 'input', 'script'):
            tag.replace_with('')
        elif 'class' in tag.attrs \
                and ('jllikeproSharesContayner' in tag['class']
                     or 'mv-social-buttons-box' in tag['class']):
            tag.replace_with('')
        elif 'id' in tag.attrs and tag['id'] == 'mc-container':
            tag.replace_with('')
    process_img(content)
    return content

def process_img(soup):
    for img in soup.find_all(name='img'):
        if img['src'].startswith('/images'):
            img['src'] = BASE_URL + img['src']

def htmlize(item, root_page, tag):
    title_tag = 'h'+str(item.depth)
    title = root_page.new_tag(title_tag)
    title.append(item.name)
    tag.append(title)
    if item.content:
        tag.append(item.content)
    for child in item.childrens:
        htmlize(child, root_page, tag)

def main():
    root_page = BeautifulSoup('<html><head></head><body></body></html>', 'lxml')
    print(type(root_page.html.body))
    table_of_content = get_table_of_content(CONTENT_URL, name='Руха')
    htmlize(table_of_content, root_page, root_page.html.body)

    with open('ruha.html', 'wb') as htmlf:
        htmlf.write(root_page.prettify('utf8'))

    """
    fb2 = pypandoc.convert_text(str(root_page), 'fb2', format='html')
    with open('ruha.fb2', 'w') as fb2f:
        fb2f.write(fb2)
    """

if __name__ == '__main__':
    main()
