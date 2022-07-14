# Importing BeautifulSoup class from the bs4 module
from bs4 import BeautifulSoup
import os

for file in os.listdir(os.path.expanduser("~/git/yorku-class-scraper/html/")):
    # Opening the html file
    HTMLFile = os.path.expanduser("~/git/yorku-class-scraper/html/") + file

    # Reading the file

    index = open(HTMLFile, 'rb').read()

    # Creating a BeautifulSoup object and specifying the parser
    S = BeautifulSoup(index, 'lxml')

    # Providing the source
    Attr = S.html.body.table.tbody

    # Using the Children attribute to get the children of a tag
    # Only contain tag names and not the spaces
    Attr_Tag = [e.text.replace("\n", "\xa0").split("\xa0") for e in Attr.children if e.name is not None]
    # Attr_Tag = [e.text for e in Attr.children if e.name is not None]


    # Printing the children
    # print(Attr_Tag)
    for i in Attr_Tag:
        print(i)
