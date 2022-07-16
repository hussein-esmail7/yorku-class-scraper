# Importing BeautifulSoup class from the bs4 module
from bs4 import BeautifulSoup
import os

def time_location_formatted(input_str):
    """
    0: Weekday
    ":"+2: time
    until letter: duration
    rest: room
    """
    weekday = input_str[0]
    input_str = input_str[1:]
    time = input_str[:input_str.index(":")+3].strip()
    input_str = input_str[len(time):]
    indexofLetter = -1
    for num, i in enumerate(input_str[2:]):
        if i.isalpha and indexofLetter == -1:
            indexofLetter = num + 3
    duration = input_str[:indexofLetter].strip()
    room = input_str[indexofLetter:].strip()
    return [weekday, time, duration, room]

def get_table_contents(filepath):
    if filepath.endswith(".html"):
        index = open(filepath, 'rb').read() # Get contents of file
        S = BeautifulSoup(index, 'lxml') # Make bs4 object using lxml parser
        Attr = S.html.body.table.tbody # Locating table row elements
        # Using the Children attribute to get the children of a tag
        # Only contain tag names and not the spaces
        Attr_Tag = [e.text.replace("\n", "\xa0").split("\xa0") for e in Attr.children if e.name is not None]
        # Attr_Tag = [e.text for e in Attr.children if e.name is not None]
        # TODO: print(time_location_formatted("W12:30180ACW 102"))
        for num, i in enumerate(Attr_Tag):
            del Attr_Tag[num][0]
            print(i)

def main():
    FILEPATH_HTML = "~/git/yorku-class-scraper/html/"
    FILEPATH_HTML = os.path.expanduser(FILEPATH_HTML)
    for file in os.listdir(FILEPATH_HTML):
        print(get_table_contents(FILEPATH_HTML + file))


if __name__ == "__main__":
    main()

