# TODO 
# Prereqs stuff: 
# african 1, 2, and 3 
# fixBrackets by checking if sub types are the same type
# add a check to see if the course exists 
#
# Merge multi-term courses (A-C suffixes)
# Merge courses and labs (L suffix)
# Merge one/two year courses (stated in grading) 

# Running a single SQL query instead of a select and several updates/deletes is significantly quicker 
# We should try to do so for some of the methods 

import re 

# Expression class 
from expression import Expression

# Constants from constants.py
from myConstants import DELETE_CODES, DELETE_PREREQ_SENTENCE 
from myConstants import DELETE_PREFIXES 
from myConstants import REMOVE_PREFIXES 
from myConstants import REMOVE_SUFFIXES 
from myConstants import DELETE_PREREQS
from myConstants import FIELDS_DICT 
from myConstants import IGNORE_ABBREVS
from myConstants import PLACEHOLDER
from myConstants import DELETE_PREREQ_SENTENCE
from myConstants import ALT_CATEGORY_DICT
from myConstants import ALPHA

# Helper methods  
from helpers import removeEmptyElements
from helpers import dbConnect

cursor, db = dbConnect()

# If debug is True, the "Flag?" prompt will appear after each prereq to check accuracy. Otherwise, the current flag will be kept
debug = False

# Fixes some issues, don't really understand why
# Smth about lazy loading 
cursor = db.cursor(buffered=True)

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
        if 99 >= number:
            division = 'lower'
        elif 199 >= number >= 100: 
            division ='upper'
        elif 299 >= number >= 200:
            division = 'graduate'
        elif 499 >= number >= 300:
            division = 'profesional'
        elif number >= 500:
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

# Gets the department using the last 2 words
def getDepartment(code1In, lastWordIn, last2WordsIn):
    # print(f"code1In: {code1In} | lastWord: {lastWordIn} | last2: {last2WordsIn}")
    # Check if other code should be used and if so, update fullPrereq
    cursor.execute("SELECT * FROM categories")
    codes = cursor.fetchall()
    # Go and check for last two words find (prevents integrative biology from being recognized as biology)
    for codeSet in codes:
        newCodes = [codeSet[0], codeSet[1], codeSet[2]]
        if last2WordsIn in newCodes:
            return newCodes[1]
    for codeSet in codes:
        newCodes = [codeSet[0], codeSet[1], codeSet[2]]
        if lastWordIn in newCodes:
            return newCodes[1]
    return code1In

# Processes boolean strings so remove the junk and retrieve the courses
def processBoolean(stringIn, code1In):
    # Fix "17a is not prerequisite to 17b" bs
    if "is not prerequisite to" in stringIn: 
        return Expression(None, [None])
    elif "may be taken before" in stringIn:
        return Expression(None, [None])

    prereqs = []
    if "is a prerequisite to" in stringIn:
        prereqs.append(stringIn.split("is a prerequisite to")[0])
    elif "is prerequisite to" in stringIn:
        prereqs.append(stringIn.split("is prerequisite to")[0])
    elif "is prerequisite for" in stringIn:
        prereqs.append(stringIn.split("is prerequisite for")[0])
    else:
        # Deal with prereqs like 201a-201c
        words = re.split('\s|\/|\(|\)', stringIn)
        for i in range(len(words)): 
            if len(words[i].split('-')) >= 2:
                # Get last words. Setting them to EMPTY works because the prereq is all lower 
                lastWord = "EMPTY"
                last2Words = "EMPTY"
                # gets the word before the course 
                if len(words[:i]) > 0:
                    lastWord = words[i-1]
                if len(words[:i-1]) > 0:
                    last2Words = words[i-2] + " " + lastWord
                department = getDepartment(code1In, lastWord, last2Words)

                courses = words[i].split('-')
                if len(courses) == 2:
                    courseCodeMatch = re.search(r"(^|\s|\(|/)[a-z]*[0-9][0-9]*", courses[0])
                    if courseCodeMatch == None:
                        break
                    courseCode = courseCodeMatch.group()
                    # Get range of letters 
                    slice = ALPHA[ALPHA.find(courses[0][-1]) : ALPHA.find(courses[1][-1]) + 1]
                    print(lastWord)
                    for letter in slice:
                        if "concurrent" in stringIn:
                            prereqs.append(department + " " + courseCode.strip().strip("()") + letter + " conc")
                        else:
                            prereqs.append(department + " " + courseCode.strip().strip("()") + letter)
                    break
                else:
                    for course in courses:
                        if "concurrent" in stringIn:
                            prereqs.append(department + " " + course.strip().strip("()") + " conc")
                        else:
                            prereqs.append(department + " " + course.strip().strip("()"))

    
    if len(prereqs) > 0:
        expressions = []
        for prereq in prereqs:
            expressions.append(createExpression(prereq, code1In))
        return Expression('and', expressions)

    # There is prob a better way to do this 
    # Put an array of tuples into courses, index 0 is the startIndex and index 2 is the text
    courses = []
    # Matches number that are surrounded by letters then are surrounded by spaces or the end/start of string
    for match in re.finditer(r"(^|\s|\(|/)[a-z]*[0-9][0-9]*[a-z]*($|\s|\))", stringIn):
        courses.append((match.start(), match.group()))

    if courses == None or len(courses) == 0:
        return Expression(None, [None])
    elif len(courses) > 1 or len(courses) == 0:
        print(f" What the fuck: {courses} |")
        return Expression(None, [None])
    else: 
        regexIndex = courses[0][0]
        # gets the word before the course 
        lastWord = "EMPTY"
        last2Words = "EMPTY"
        words = re.split("\s|/|\(|\)", stringIn[:regexIndex])
        if len(words) >= 1:
            lastWord = words[-1].strip()
        if len(words) >= 2:
            last2Words = words[-2].strip() + " " + lastWord
        
        nextWords = stringIn[regexIndex:].split(" ")
        # Ignore the number if the next word is units
        if len(nextWords) > 1:
            nextWord = stringIn[regexIndex:].split(" ")[1].strip()
            if nextWord.startswith("units"):
                return Expression(None, [None])

        # Set prereq using codeIn
        course = courses[0][1].strip().strip("()")
        if "concurrent" in stringIn:
            course += " conc"
        fullPrereq = getDepartment(code1In, lastWord, last2Words) + " " + course

        # Strip stuff on the ends, just in case 
        fullPrereq = fullPrereq.strip(" .,;")
        return Expression("boolean", [fullPrereq])

# Recursive method that creates the expression objects
# It will continually go deeper into "and"/"or" statements until it gets to the raw prereqs 
def createExpression(newPrereqIn, code1In):
    # Key: word that shows up in prereqs | Value : type of operator 
    operators = {' and ':'and', ' plus ':'and', ' & ':'and', 'as well as ':'and',' or ':'or', ' and/or ':'or', '/':'or'}

    # check for chained operators
    for operator in operators:
        # Stores the indivdual sections of a chained statement 
        rawExpressions = []

        # Find chained operator
        opIndex = newPrereqIn.find(operator)
        while opIndex != -1:

            if newPrereqIn[opIndex - 1] == ",":
                index = opIndex - 1

                # Find a terminating character and add add section of the chain to rawExpressions
                # regex = re.compile(".|and|or")
                # match = regex.search(newPrereqIn[index + len(operator):])
                # start = match.start()
                # if start != 0:
                #     rawExpressions.append(newPrereqIn[index + len(operator):index + len(operator) + start])
                #     rawExpressions.append(newPrereqIn[index + len(operator) + start:])
                # else:
                #     rawExpressions.append(newPrereqIn[index + len(operator):])
                rawExpressions.extend(newPrereqIn[index:].split(','))
                rawExpressions.extend(newPrereqIn[:index].split(','))
                break
            else:
                opIndex = newPrereqIn.find(operator, opIndex + 1)

        # If a chained "and" was found, create expressions 
        if len(rawExpressions) > 0:
            expressions = []
            for rawExpression in rawExpressions:
                expressions.append(createExpression(rawExpression.strip(), code1In))
            return Expression(operators[operator], expressions)
    
    # Checks for non-chained in order of op precedence 
    for operator in operators:
        opIndex = newPrereqIn.find(operator)
        while opIndex != -1:
            # Ignore chained operator (a, b, and/or c)
            if newPrereqIn[opIndex - 1] == ",":
                # Find the next operator if it exists 
                opIndex = newPrereqIn.find(operator, opIndex + 1) 
                continue
            else: 
                # Splits the string around the operator into two separate expressions 
                return Expression(operators[operator], [createExpression(newPrereqIn[:opIndex], code1In), createExpression(newPrereqIn[opIndex + len(operator):], code1In)])
    
    # FOR DEBUGGING ONLY (AND IT HAS NEVER BEEN CALLED WOOHOO)
    if ' and ' in newPrereqIn or ' or ' in newPrereqIn:
        print("This should have returned by now because it has and/or...")
        print(newPrereqIn)

    # For stuff like anthro 1, bio 2
    commaSplit = newPrereqIn.split(', ')
    if len(commaSplit) > 1:
        expressions = []
        for prereq in commaSplit:
            expressions.append(processBoolean(prereq, code1In))
        return Expression("and", expressions)
    else:
        # Strip stuff on the ends, just in case 
        newPrereqIn = newPrereqIn.replace(PLACEHOLDER, "")
        newPrereqIn = newPrereqIn.strip(" .,;")
        return (processBoolean(newPrereqIn, code1In))

def scSplit(prereqs):
    # Deals with stupid awful ;
    splitExpressions = []
    for prereq in prereqs:
        if prereq.find("; or") != -1:
            splitExpressions.append(["or", scSplit(prereq.split("; or"))])
        elif prereq.find(";") != -1:
            splitExpressions.append(["and", scSplit(prereq.split(";"))])
        else:
            splitExpressions.append(["boolean", [prereq]])

    # remove if it has score in it
    for i in range(len(splitExpressions)):
        j = 0
        while j < len(splitExpressions[i][1]):
            for delPrereq in DELETE_PREREQ_SENTENCE:
                if splitExpressions[i][1][j].find(delPrereq) != -1:
                    del splitExpressions[i][1][j]
                    j -= 1
                    break
            j += 1

    # Processes the prereqs after the ; are dealt with 
    finalPrereqs = []
    for splitExpression in splitExpressions:
        subFinalPrereqs = []
        for newPrereq in splitExpression[1]:
            print(f"in: {newPrereq} \n", end="")
            subFinalPrereqs.append(createExpression(newPrereq, code1))
        if len(splitExpression[1]) == 0:
            subFinalPrereqs.append(None)
        
        if splitExpression[0] == "and":
            finalPrereqs.append(Expression("and", subFinalPrereqs))
        elif splitExpression[0] == "or":
            finalPrereqs.append(Expression("or", subFinalPrereqs))
        else:
            finalPrereqs.append(subFinalPrereqs[0])
    
    return splitExpressions

def processPrereqs():
    cursor.execute("SELECT * FROM prereqs_p where flag = true")
    entries = cursor.fetchall()
    for entry in entries: 
        prereq = entry[1] 
        cursor.execute("SELECT code1 FROM course_codes_p WHERE id = %s", (entry[0],))

        # Returns a tuple so the [0] is neccessary
        code1 = cursor.fetchone()[0]

        # Ignore blank prereqs
        # TODO: Copy blank prereqs into the processed table 
        if len(prereq) == 0:
            continue

        for delPre in DELETE_PREREQS:
            prereq = prereq.replace(delPre, PLACEHOLDER)

        # Split sentences 
        # TODO: fix this mess 
        splitPrereqs = []
        lastIndex = 0
        for i in range(len(prereq)):
            skip = False
            if prereq[i : i + 2] == ". ":
                for abbrev in IGNORE_ABBREVS:
                    for j in range(len(abbrev)):
                        if abbrev[j] == ".":
                            if prereq[i - j:i - j + len(abbrev)] == abbrev:
                                # wtf am i doing 
                                skip = True
                                break
                    if skip == True:
                        break
                if not skip:
                    splitPrereqs.append(prereq[lastIndex:i])
                    lastIndex = i + 2
                    skip = False
        splitPrereqs.append(prereq[lastIndex:])

        # Deals with stupid awful ;
        splitExpressions = []
        for prereq in splitPrereqs:
            if prereq.find("; or") != -1:
                splitExpressions.append(["or", prereq.split("; or")])
            elif prereq.find(";") != -1:
                splitExpressions.append(["and", prereq.split(";")])
            else:
                splitExpressions.append(["boolean", [prereq]])
        
        # remove if it has score in it
        for i in range(len(splitExpressions)):
            j = 0
            while j < len(splitExpressions[i][1]):
                for delPrereq in DELETE_PREREQ_SENTENCE:
                    if splitExpressions[i][1][j].find(delPrereq) != -1:
                        del splitExpressions[i][1][j]
                        j -= 1
                        break
                j += 1

        # Processes the prereqs after the ; are dealt with 
        print(f"\nold: {entry[1]} \n", end="")
        finalPrereqs = []
        for splitExpression in splitExpressions:
            subFinalPrereqs = []
            for newPrereq in splitExpression[1]:
                print(f"in: {newPrereq} \n", end="")
                subFinalPrereqs.append(createExpression(newPrereq, code1))
            if len(splitExpression[1]) == 0:
                subFinalPrereqs.append(None)
            
            if splitExpression[0] == "and":
                finalPrereqs.append(Expression("and", subFinalPrereqs))
            elif splitExpression[0] == "or":
                finalPrereqs.append(Expression("or", subFinalPrereqs))
            else:
                finalPrereqs.append(subFinalPrereqs[0])
        
        if len(finalPrereqs) > 0:
            finalExpression = Expression("and", finalPrereqs)
        else:
            finalExpression = finalPrereqs[0]

        print(f"pre-fix: {finalExpression.getFullExpression()}")

        finalExpression.fixBrackets()

        print(f"new: {finalExpression.getFullExpression()}")

        if debug == True:
            flag = input("Flag? ")

        if debug == True and flag == "":
            cursor.execute("UPDATE prereqs_p SET flag = false WHERE id = %s", (entry[0], ))
            db.commit()

        cursor.execute("UPDATE prereqs_p SET prereq = %s WHERE id = %s", (finalExpression.getFullExpression(), entry[0]))
        db.commit()

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
#updateFields()
processPrereqs()