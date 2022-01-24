# COURSE DIRECTORY EXAMPLE:
# <div id="atozindex">
#   <h2 class="letternav-head" id="A">...</h2>
#   <ul>
#       <li>
#           <a href="/courses/x">...</a>
#       </li>
#   </ul>
#   ...
# </div>

# COURSE BLOCK EXAMPLE:
# <div class="courseblock">
#   ...
#       <h3 class="courseblocktitle">
#           <span class="code">...</span>
#           <span class="title">...</span>
#           <span class="hours">...</span>
#       </h3>
#   <div class="coursebody"...>
#       <div class="coursedetails"...>
#           <div class="course-section">
#               ...
#               <p>...</p>
#           </div>
#       </div>
#   </div>
# </div>

from bs4 import BeautifulSoup

from time import sleep
from os import environ
import requests

from dotenv import load_dotenv

import mysql.connector

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

# Remove letters to skip them 
LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

DIR_URL = "http://guide.berkeley.edu/courses/"
ROOT_URL = "http://guide.berkeley.edu"
SCHOOL_YEAR = 2021

def getCodes(fullCodeIn):
    code1 = fullCodeIn[:fullCodeIn.rindex(' ')].lower()
    code2 = fullCodeIn[fullCodeIn.rindex(' ') + 1:].lower()
    return [fullCodeIn, code1, code2]

linksDict = {}
# Get the directory page 
dirReq = requests.get(DIR_URL)
soup = BeautifulSoup(dirReq.content, 'html.parser')
atoz = soup.find('div', {'id':'atozindex'})
categoryGroups = atoz.find_all('ul')
alphas = atoz.find_all('h2')
for i in range(len(categoryGroups)):
    alpha = alphas[i].get('id')
    links = []
    categories = categoryGroups[i].find_all('a')
    for category in categories:
        links.append(category.get('href'))
    linksDict[alpha] = links
print(linksDict)

for key in linksDict:
    if key not in LETTERS:
        continue
    for link in linksDict[key]:
        linkReq = requests.get(ROOT_URL + link)
        soup = BeautifulSoup(linkReq.content, 'html.parser')
        
        # Gets the container for all of the courses 
        courses = soup.find_all('div', {'class':'courseblock'})
        for course in courses:
            # basicInfo in the parent of the spans with course info 
            basicInfo = course.find('h3', {'class':'courseblocktitle'})

            # code1 is the prefix, such as AEROSPC and code2 is the actual code, such as 1A
            fullCode = basicInfo.find('span', {'class':'code'}).getText()
            fullCode = fullCode.replace('\u00a0', ' ').lower()
            listings = [getCodes(fullCode)]

            # title is not processed 
            title = basicInfo.find('span', {'class':'title'}).getText()

            # units is stripped of text to become an integer 
            units = basicInfo.find('span', {'class':'hours'}).getText()
            units = units[:units.index(' ')]

            # Get the description and terms 
            description = course.find('p', {'class':'courseblockdesc'}).getText()
            descriptions = description.split('\n')
            
            # Set to false to avoid errors later 
            fall = False
            spring = False
            summer = False
            
            if f"fall {SCHOOL_YEAR}" in descriptions[0].lower():
                fall = True
            if f"spring {SCHOOL_YEAR + 1}" in descriptions[0].lower():
                spring = True
            if f"summer {SCHOOL_YEAR + 1}" in descriptions[0].lower():
                summer = True
            
            # Some older courses have two line breaks, with a blank line between them and this fixed that 
            if descriptions[1] == '':
                description = descriptions[2]
            else:
                description = descriptions[1]
            #print(f"{fullCode}: {descriptions}")

            # Set variables to None to avoid problems later 
            prereqs = None
            subject = None
            level = None
            grading = None
            final = None

            # details has more advanced info such as prereqs 
            sections = course.find('div', {'class':'coursedetails'}).findChildren('div', recursive=False)
            for section in sections:
                details = section.findChildren('p', recursive=False)
                heading = details[0].getText

                for i in range(1, len(details)):
                    subHeading = details[i].find('strong').getText()
                    # Example: 'Prerequisites: 135A is a prerequisite to 135B or consent of instructor'
                    # prereq = 135a is a prerequisite to 135b or consent of instructor
                    if subHeading == "Prerequisites:":
                        prereqs = details[i].getText()[len(subHeading) + 1:].lower()
                    # Example: 'Subject/Course Level: Aerospace Studies/Undergraduate'
                    # subject = 'aerospace studies'
                    # level = 'undergraduate'
                    elif subHeading == "Subject/Course Level:":
                        temp = details[i].getText()[len(subHeading) + 1:]
                        subject = temp[:temp.rindex('/')].lower()
                        level = temp[temp.rindex('/') + 1:].lower()
                    # Example: 'Grading/Final exam status: Letter grade. Final exam required.'
                    # grading = 'letter grade' 
                    # final = 'final exam required'
                    elif subHeading == "Grading/Final exam status:":
                        temp = details[i].getText()[len(subHeading) + 1:]
                        # The easiest way to check if only a final is listed. From what I've seen, if there is one period it's only talking about the final 
                        # Second e.g. check fixes MUSIC R1B
                        if temp.count('.') == 1 or 'e.g.' in temp:
                            final = temp[:-2].lower()
                        else:
                            grading = temp[:temp.index('.')].lower()
                            final = temp[temp.index('.') + 2:-2].lower()
                    # Example: Grading: Letter grade.
                    # grading = letter grade
                    elif subHeading == "Grading:":
                        grading = details[i].getText()[len(subHeading) + 1:][:-2].lower()
                    # Example: Also listed as: Code1/Code2
                    # listings = [fullCode, fullCode1, fullCode3]
                    elif subHeading == "Also listed as:":
                        altCodes = details[i].getText()[len(subHeading) + 1:].lower().replace("\xa0", " ").split("/")
                        for code in altCodes:
                            listings.append(getCodes(code))
            
            print(f"fullCode: {fullCode} | title: {title} | description: {description[:10]} | units: {units} | subject: {subject} | level: {level} | fall: {fall} | spring: {spring} | summer: {summer} | grading: {grading} | final: {final} | listings: {listings}")
            
            cursor.execute("""SELECT * FROM course_codes WHERE full_code=%s""", (fullCode,))
            entries = cursor.fetchall()

            # If the course code is in course_codes, it's safe to assume that its been added to all tables 
            if len(entries) == 0:
                   
                #Insert infomation into courses 
                cursor.execute("""INSERT INTO courses
                                (title, description, units, subject, level, fall, spring, summer, grading, final) 
                                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE description=%s, units=%s, subject=%s, level=%s, fall=%s, spring=%s, summer=%s, grading=%s, final=%s""", 
                                (title, description, units, subject, level, fall, spring, summer, grading, final,
                                description, units, subject, level, fall, spring, summer, grading, final))
                #print(cursor.statement)
                db.commit()

                # The ID assigned by MYSQL to the last row, used to connect it to other tables 
                lastID = cursor.lastrowid

                # Insert into prereqs 
                if prereqs != None:
                    cursor.execute("""INSERT INTO prereqs (id, prereq) VALUES(%s, %s) """, 
                                    (lastID, prereqs))
                    db.commit()

                # Insert all course codes into course_codes
                for listing in listings:
                    if entries == 0:
                        cursor.execute("""INSERT INTO course_codes (id, full_code, code1, code2) VALUES(%s, %s, %s, %s)""",
                                        (lastID, listing[0], listing[1], listing[2]))
                        db.commit()