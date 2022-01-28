# TO DO 
# - Merge multi-term courses (A-C suffixes)
# - Merge courses and labs (L suffix)

# NONE OF THIS HAS BEEN TESTED 

import mysql.connector
from dotenv import load_dotenv
from os import environ
import string

# Codes to be deleted, regardless of suffix of prefix 
DELETE_CODES = ['24', '39', '84', '97', '98', '99', '197', '198', '199']

# All courses with these prefixes will be deleted 
DELETE_PREFIXES = ['h', 'n']

# Remove these prefixes from course codes
REMOVE_PREFIXES = ['r'] 

# Remove these suffixes from course codes
REMOVE_SUFFIXES = ['ac']

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

# Deletes all entries with the given ID 
def deleteID(idIn):
    cursor.execute("DELETE FROM courses_p WHERE id = %s", (idIn))
    cursor.execute("DELETE FROM course_codes_p WHERE id = %s", (idIn))
    cursor.execute("DELETE FROM prereqs_p WHERE id = %s", (idIn))
    db.commit()

# Deletes based on DELETE_CODES
def deleteOnCode():
    query = """SELECT id FROM courses_p
                INNER JOIN course_codes_p USING (id) 
                WHERE REGEXP_LIKE(code2, '^(%s).*') 
                GROUP BY id"""
    query = query % '|'.join(DELETE_CODES)
    cursor.execute(query)
    ids = cursor.fetchall()
    for id in ids:
        deleteID(id)

# Deletes based on DELETE_PREFIXES
def deleteOnPrefix():
    query = """SELECT id FROM courses_p
                INNER JOIN course_codes_p USING (id) 
                WHERE REGEXP_LIKE(code2, '^(%s).*') 
                GROUP BY id"""
    query = query % '|'.join(DELETE_PREFIXES)
    cursor.execute(query)
    ids = cursor.fetchall()
    for id in ids:
        deleteID(id)

# Add divisions to entries based on the course code 
# I think this will do cross section courses twice, but that shouldn't matter (but should prob be fixed)
def addDivision(): 
    cursor.execute("""SELECT id, code2 FROM courses_p
                    INNER JOIN course_codes_p USING (id)
                    WHERE division IS NULL""")
    entries = cursor.fetchall()
    for entry in entries:
        # Removes all letters from the beginning and end of the string 
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
        elif 699 >= number >= 500:
            deleteID(entries[0])
            continue
        else:
            print("Error occurred, fix it")
            exit()
        cursor.execute("UPDATE courses_p SET division = %s WHERE id = %s", (division, entry[0]))
        db.commit()

# Removes prefixes based on REMOVE_PREFIXES
def removePrefixes():
    # Regex: Must start with one of the prefixes then have anything after. Will match if the code has one of the prefixes  
    query = "SELECT course_code_id, full_code, code2 FROM course_codes_p WHERE REGEXP_LIKE(code2, '^(%s).*')"
    query = query % "|".join(REMOVE_PREFIXES)
    cursor.execute(query)
    entries = cursor.fetchall()
    
    for entry in entries:
        # Removes the first char of the codes 
        newFullCode = entry[1][entry[1].index(' ') + 2:]
        newCode2 = entry[2][1:]

        cursor.execute("UPDATE course_codes_p SET full_code = %s, code2 = %s WHERE id = %s", (newFullCode, newCode2, entries[0]))
        db.commit()

# Removes suffixes based on REMOVE_SUFFIXES
def removeSuffixes():
    # Regex: Must be one number then any number of numbers, then the suffix. Will match if the code has one of the suffixes 
    query = "SELECT course_code_id, full_code, code2 FROM course_codes_p WHERE REGEXP_LIKE(code2, '[0-9][0-9]*(%s')"
    query = query % "|".join(REMOVE_SUFFIXES)
    cursor.execute(query)
    entries = cursor.fetchall()

    for entry in entries:
        # Removes all letters from the beginning and end of code2, giving the course number 
        number = entry[2].strip(alpha)
        # Removes the suffix from the codes
        newFullCode = entry[1][:entry[1].index(number + len(number))]
        newCode2 = entry[2][:entry[2].index(number + len(number))]

        cursor.execute("UPDATE course_codes_p SET full_code = %s, code2 = %s WHERE id = %s", (newFullCode, newCode2, entries[0]))
        db.commit()

# Call all processing methods 
deleteOnCode()
deleteOnPrefix()
addDivision()
removePrefixes()
removeSuffixes()
