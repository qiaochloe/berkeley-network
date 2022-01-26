# TO DO 
# - Remove Reading and Composition prefix (R)
# - Remove American Cultures suffix (AC)
# - Merge multi-term courses (A-C suffixes)
# - Merge courses and labs (L suffix)
# - Sort by lower division (1-99), upper division (100-199), graduate (200-299), professional (300-499)
# - Delete Individual Study and Research Graduate courses (500-699)

# NONE OF THIS HAS BEEN TESTED 

import mysql.connector
from dotenv import load_dotenv
from os import environ
import re 
import string

# Codes to be deleted, regardless of suffix of prefix 
DELETE_CODES = [24, 39, 84, 97, 98, 99, 197, 198, 199]

# All courses with these prefixes will be deleted 
DELETE_PREFIXES = ['h', 'n']

alpha = string.ascii_lowercase

# Load env constants
load_dotenv()
DB_NAME = environ.get("databaseName")
HOST = environ.get("host")
USER = environ.get("user")
PASSWORD = environ.get("password")

# Connect to DB
db = mysql.connector.connect(
    host=HOST,
    user=USER,
    password=PASSWORD,
    database=DB_NAME
)
cursor = db.cursor()

def deleteOnCode():
    query = "DELETE FROM courses_processed WHERE REGEXP_LIKE(code2, '^[a-z](%s)[a-z]*')"
    query % '|'.join(DELETE_CODES)
    cursor.execute(query)
    db.commit()

def deleteOnPrefix():
    query = "DELETE FROM courses_processed WHERE REGEXP_LIKE(code2, '^(%s).*')"
    query % '|'.join(DELETE_PREFIXES)
    cursor.execute(query)
    db.commit()

def addDivision():
    cursor.execute("SELECT id, code2 FROM courses_processed WHERE division IS NULL")
    entries = cursor.fetchall()
    for entry in entries:
        number = int(entry[1].strip(alpha))
        division = None
        if 99 >= number >= 1:
            division = 'lower'
        elif 199 >= number >= 100: 
            division ='upper'
        elif 299 >= number >= 200:
            division = 'graduate'
        elif 499 >= number >= 300:
            division = 'profesional'
        else:
            print("Error occured, fix it")
            exit()
        cursor.execute("UPDATE courses_processed SET division = %s WHERE id = %s", (division, entry[0]))
        db.commit()

deleteOnCode()
deleteOnPrefix()
