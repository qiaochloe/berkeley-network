# TO DO 
# - Merge multi-term courses (A-C suffixes)
# - Merge courses and labs (L suffix)
# Merge one/two year courses (stated in grading) 

# Running a single SQL query instead of a select and several updates/deletes is significantly quicker 
# We should try to do so for some of the methods 

from asyncio import constants
import mysql.connector
from dotenv import load_dotenv
from os import environ

# Constants from constants.py
from myConstants import DELETE_CODES 
from myConstants import DELETE_PREFIXES 
from myConstants import REMOVE_PREFIXES 
from myConstants import REMOVE_SUFFIXES 
from myConstants import DELETE_PREREQS
from myConstants import FIELDS_DICT 

from myConstants import ALPHA

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

# Processes arrays for removing prereqs
def processArray(array):
    # Remvoes empty strings from an array 
    out = [i.strip(',. ') for i in array]
    out = [i for i in out if i]
    return out

# Deletes all entries with the given ID 
def deleteID(idIn):
    cursor.execute("DELETE FROM courses_p WHERE id = %s", (idIn,))
    cursor.execute("DELETE FROM course_codes_p WHERE id = %s", (idIn,))
    cursor.execute("DELETE FROM prereqs_p WHERE id = %s", (idIn,))
    db.commit()

# Deletes based on DELETE_CODES
def deleteOnCode():
    query = """SELECT id, full_code FROM courses_p
                INNER JOIN course_codes_p USING (id) 
                WHERE REGEXP_LIKE(code2, '^(%s)([a-z]| )[a-z]*') 
                GROUP BY id"""
    query = query % '|'.join(DELETE_CODES)
    cursor.execute(query)
    entries = cursor.fetchall()
    for entry in entries:
        print(f"Deleting {entry[0]} because of its code {entry[1]}")
        deleteID(entry[0])

# Deletes based on DELETE_PREFIXES
def deleteOnPrefix():
    query = """SELECT id, full_code FROM courses_p
                INNER JOIN course_codes_p USING (id) 
                WHERE REGEXP_LIKE(code2, '^(%s).*') 
                GROUP BY id"""
    query = query % '|'.join(DELETE_PREFIXES)
    cursor.execute(query)
    entries = cursor.fetchall()
    for entry in entries:
        print(f"Deleting {entry[0]} because of its prefix {entry[1]}")
        deleteID(entry[0])

# Add divisions to entries based on the course code 
# I think this will do cross section courses twice, but that shouldn't matter (but should prob be fixed)
def addDivision(): 
    cursor.execute("""SELECT id, code2 FROM courses_p
                    INNER JOIN course_codes_p USING (id)
                    WHERE division IS NULL""")
    entries = cursor.fetchall()
    for entry in entries:
        # Removes all letters from the beginning and end of the string 
        number = int(entry[1].strip(ALPHA))
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
            print(f"Deleting {entry[1]} because of its division")
            deleteID(entry[0])
            continue
        else:
            print("Error occurred, fix it")
            exit()
        print(f"Setting division to {division} for course id {entry[0]}")
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
        newCode2 = entry[2][1:]
        newFullCode = entry[1][:entry[1].index(' ')] + newCode2

        print(f"Updating {entry[1]} to {newFullCode} for code id {entry[0]} (rmp)")
        cursor.execute("UPDATE course_codes_p SET full_code = %s, code2 = %s WHERE course_code_id = %s", (newFullCode, newCode2, entry[0]))
        db.commit()

# Removes suffixes based on REMOVE_SUFFIXES
def removeSuffixes():
    # Regex: Must be one number then any number of numbers, then the suffix. Will match if the code has one of the suffixes 
    query = "SELECT course_code_id, full_code, code2 FROM course_codes_p WHERE REGEXP_LIKE(code2, '[0-9][0-9]*(%s)')"
    query = query % "|".join(REMOVE_SUFFIXES)
    cursor.execute(query)
    entries = cursor.fetchall()

    for entry in entries:
        # Removes all letters from the beginning and end of code2, giving the course number 
        number = entry[2].strip(ALPHA)
        # Removes the suffix from the codes
        newCode2 = entry[2][:entry[2].index(number) + len(number)]
        newFullCode = entry[1][:entry[1].index(number) + len(number)]

        print(f"Updating {entry[1]} to {newFullCode} for code id {entry[0]} (rms)")
        cursor.execute("UPDATE course_codes_p SET full_code = %s, code2 = %s WHERE course_code_id = %s", (newFullCode, newCode2, entry[0]))
        db.commit()

# Updates fields according to the FIELDS_DICT
def updateFields():
    for column in FIELDS_DICT:
        for key, value in column[1].items():
            # There is prob a better way to do with, but just checking for the string 'delete' works 
            if value == 'delete':
                query = "SELECT id, %s FROM courses_p WHERE %s = '%s'" % (column[0], column[0], key)
                cursor.execute(query)
                entries = cursor.fetchall()
                for entry in entries: 
                    print(f"Deleting {entry[0]} because of its {column[0]} {entry[1]}")
                    deleteID(entry[0])
                continue

            # Normally you could just pass the values into cursor.execute, however that inserts them with " " which we don't want
            query = "UPDATE courses_p SET %s = '%s' WHERE %s = '%s'" % (column[0], value, column[0], key)
            print(f"Query: {query}")
            cursor.execute(query)
            db.commit()

def processPrereqs():
    cursor.execute("SELECT * FROM prereqs_p")
    entries = cursor.fetchall()
    for entry in entries: 
        prereq = entry[1] 
        if len(prereq) == 0:
            continue
        newPrereq = prereq
        for substring in DELETE_PREREQS:
            newPrereq = newPrereq.replace(substring, "")
            
        # THIS IS BAD BAD I SHOULD JUST FIGURE OUT AN ALGO INSTEAD OF RANDOMLY CODING
        if ' or ' in prereq and ' and ' in prereq:
            orGroups = newPrereq.split(" or ")
            andGroups = []
            for orGroup in orGroups:
                andGroups.extend(orGroup.split(" and "))
            orGroups = processArray(orGroups)
            andGroups = processArray(andGroups)
            print(f"prereq: {prereq} | newPrereq: {newPrereq} | orGroups: {orGroups} | andGroups: {andGroups}")
        elif  ' and ' in prereq:
            andGroups = newPrereq.split(" or ")
            andGroups = processArray(andGroups)
            print(f"prereq: {prereq} | newPrereq: {newPrereq} | orGroups: {andGroups}")
        elif ' or ' in prereq:
            orGroups = newPrereq.split(" or ")
            andGroups = []
            for orGroup in orGroups:
                andGroups.extend(orGroup.split(" and "))
            orGroups = processArray(orGroups)
            print(f"prereq: {prereq} | newPrereq: {newPrereq} | orGroups: {orGroups}")
        else:
            print(f"prereq: {prereq} | newPrereq: {newPrereq}")

# Unfinished: requires processing prereqs
def mergeCourses():
    cursor.execute("SELECT DISTINCT code1 FROM course_codes_p")
    code1s = cursor.fetchall()
    for code1 in code1s:
        cursor.execute("SELECT code2 from course_codes_p WHERE code1 = %s", (code1,))
        code2s = cursor.fetchall()
        #for code2 in code2s:
            #if code2[-1] in ['a', 'b', 'c']:


# Call all processing methods 
deleteOnCode()
deleteOnPrefix()
addDivision()
removePrefixes()
removeSuffixes()
processPrereqs()
updateFields()