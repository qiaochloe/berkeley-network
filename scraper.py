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
            code1 = fullCode[:fullCode.rindex(' ')].lower()
            code2 = fullCode[fullCode.rindex(' ') + 1:].lower()

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
            listings = [fullCode]

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
                        
                    elif subHeading == "Also listed as:":
                        listings.extend(details[i].getText()[len(subHeading) + 1:].lower().replace("\xa0", " ").split("/"))
                    # Example: Also listed as: Code1/Code2
                    # listings = [fullCode, Code1, Code2]
            
            print(f"fullCode: {fullCode} | code1: {code1} | code2: {code2} | title: {title} | description: {description[:10]} | units: {units} | subject: {subject} | level: {level} | fall: {fall} | spring: {spring} | summer: {summer} | grading: {grading} | final: {final} | listings: {listings}")
            
            cursor.execute("""INSERT INTO courses
                            (code1, code2, title, description, units, subject, level, fall, spring, summer, grading, final) 
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE description=%s, units=%s, subject=%s, level=%s, fall=%s, spring=%s, summer=%s, grading=%s, final=%s""", 
                            (code1, code2, title, description, units, subject, level, fall, spring, summer, grading, final,
                             description, units, subject, level, fall, spring, summer, grading, final))
            #print(cursor.statement)
            db.commit()
            #if prereqs != None:
            #    cursor.execute("""INSERT INTO prereqs (course_code, prereq) VALUES(%s, %s) 
            #                    ON DUPLICATE KEY UPDATE prereq=%s""", 
            #                    (fullCode, prereqs, 
            #                    prereqs))
            #    db.commit()
