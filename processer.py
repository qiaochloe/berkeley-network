# TO DO 
# - Merge multi-term courses (A-C suffixes)
# - Merge courses and labs (L suffix)
# Merge one/two year courses (stated in grading) 

# Running a single SQL query instead of a select and several updates/deletes is significantly quicker 
# We should try to do so for some of the methods 

from asyncio import constants
from distutils.dep_util import newer_pairwise
from math import exp
import mysql.connector
from dotenv import load_dotenv
from os import environ
import re 

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

class expression:
    def __init__(self, type, subExpressions):
        self.type = type
        self.subExpressions = subExpressions

    # Get the full expression, formatted as a string 
    def getFullExpression(self):
        if self.type == "boolean":
            return self.subExpressions
        expression = f"{self.type}"
        for subExpression in self.subExpressions:
            expression += f"[{subExpression.getFullExpression()}]"
        return expression

    # TODO: requires a list of completed courses  
    def evaluateExpression(self):
        if self.type == "or":
            return None
        elif self.type == "and":
            return None
        elif self.type == "boolean":
            return None

def createExpression(newPrereq):
    andIndex = newPrereq.index("and")
    orIndex = newPrereq.index("or")
    while andIndex != -1:
        if newPrereq[andIndex - 2] == ",":
            andIndex = newPrereq[andIndex + 1:].index("and")
            continue
        else: 
            return expression("and", (createExpression(newPrereq[:andIndex]), createExpression(newPrereq[andIndex + 3:])))

    while orIndex != -1:
        if newPrereq[orIndex - 2] == ",":
            orIndex = newPrereq[orIndex + 1:].index("or")
            continue
        else: 
            return expression("or", (createExpression(newPrereq[:orIndex]), createExpression(newPrereq[orIndex + 3:])))
    
    andIndex = newPrereq.index("and")
    orIndex = newPrereq.index("or")
    rawExpressions = []
    while andIndex != -1:
        if newPrereq[andIndex - 2] == ",":
            index = newPrereq.index(", and")
        regex = re.compile(".|and|or")

        match = regex.search(newPrereq[index + 5:])

        lastIndex = index
        for i in range(index, 0, -1):
            if newPrereq[i - 3 : i] == "and" or newPrereq[i - 2 : i] == "or":
                break
            if newPrereq[i] == ",":
                rawExpressions.append(newPrereq[i + 1 : lastIndex])
                lastIndex == i
    if len(rawExpressions) > 0:
        expressions = []
        for rawExpression in rawExpressions:
            expressions.append(createExpression(rawExpression))
        return expression("and", expressions)
    
    while orIndex != -1:
        if newPrereq[orIndex - 2] == ",":
            index = newPrereq.index(", and")
            regex = re.compile(".|and|or")

            match = regex.search(newPrereq[index + 5:])

            lastIndex = index
            for i in range(index, 0, -1):
                if newPrereq[i - 3 : i] == "and" or newPrereq[i - 2 : i] == "or":
                    break
                if newPrereq[i] == ",":
                    rawExpressions.append(newPrereq[i + 1 : lastIndex])
                    lastIndex == i
    
    if len(rawExpressions) > 0:
        expressions = []
        for rawExpression in rawExpressions:
            expressions.append(createExpression(rawExpression))
        return expression("and", expressions)
    
    # FOR DEBUGGING ONLY 
    if 'and' in newPrereq or 'or' in newPrereq:
        print("This should have returned by now because it has and/or...")
        print(newPrereq)

    # Remove unneeded prereqs 
    for prereq in DELETE_PREREQS:
        if prereq in newPrereq:
            newPrereq.replace(prereq, "")

    newPrereq.strip(" .,")

    # This is not done, but I want to see if this is working so far
    return expression("boolean", newPrereq)

def processPrereqs():
    cursor.execute("SELECT * FROM prereqs_p")
    entries = cursor.fetchall()
    for entry in entries: 
        prereq = entry[1] 
        if len(prereq) == 0:
            continue

        splitPrereqs = prereq.split(".")

        finalExpression = None

        for newPrereq in splitPrereqs:
            andIndex = newPrereq.index("and")
            orIndex = newPrereq.index("or")

            while andIndex != -1:
                if newPrereq[andIndex - 2] == ",":
                    andIndex = newPrereq[andIndex + 1:].index("and")
                    continue
                else: 
                    finalPrereq = expression("and", (createExpression(newPrereq[:andIndex]), createExpression(newPrereq[andIndex + 3:])))
                    break

            while orIndex != -1:
                if newPrereq[orIndex - 2] == ",":
                    orIndex = newPrereq[orIndex + 1:].index("or")
                    continue
                else: 
                    finalPrereq = expression("or", (createExpression(newPrereq[:orIndex]), createExpression(newPrereq[orIndex + 3:])))
                    break

            finalPrereq = createExpression(newPrereq)
        print(finalPrereq.getFullExpression())

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