from bs4 import BeautifulSoup
import requests

# Constants from constants.py
from myConstants import LETTERS 
from myConstants import DIR_URL 
from myConstants import ALT_CATEGORY_DICT

from helpers import dbConnect
cursor, db = dbConnect()

dirReq = requests.get(DIR_URL)
soup = BeautifulSoup(dirReq.content, 'html.parser')
atoz = soup.find('div', {'id':'atozindex'})
categoryGroups = atoz.find_all('ul')
for categoryGroup in categoryGroups:
    cateogories = categoryGroup.find_all('li')
    for category in cateogories:
        text = category.find('a').getText().lower()
        long = text[:text.index("(")].strip()
        short = text[text.index("(") + 1 : text.index(")")]
        alt = None
        if short in ALT_CATEGORY_DICT:
            alt = ALT_CATEGORY_DICT[short]
        cursor.execute("SELECT * FROM categories WHERE short = %s", (short,))
        if len(cursor.fetchall()) == 0:
            cursor.execute("INSERT INTO categories (long_s, short, alt) VALUES (%s, %s, %s)", (long, short, alt))
            db.commit()