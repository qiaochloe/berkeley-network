# TODO
# Get links using bs4 instead of Selenium 

from selenium import webdriver
from selenium.webdriver.common.by import By

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

# The indices are NOT 0 indexed, they are 1 indexed instead 
COURSE_ALPHA =  "//div[@id='atozindex']/ul"
COURSE_CATEGORIES = "./li/a"
COURSE_HEADER = "../h2[{index}]"

EXPAND_BTN = "//button[@class='btn_expandAll]"
COURSE = "//div[@class='courseblock]"

browser = webdriver.Chrome()
browser.get("http://guide.berkeley.edu/courses/")

linksDict = {}
alphas = browser.find_elements(By.XPATH, COURSE_ALPHA)
for i in range(len(alphas)):
    id = alphas[i].find_element(By.XPATH, COURSE_HEADER.format(index=i+1)).get_attribute('id')
    categories = alphas[i].find_elements(By.XPATH, COURSE_CATEGORIES)
    links = []
    for category in categories:
        links.append(category.get_attribute('href'))
    linksDict[id] = links

browser.quit()

for key in linksDict:
    for link in linksDict[key]:
        req = requests.get(link)
        soup = BeautifulSoup(req.content, 'html.parser')
        
        # Gets the container for all of the courses 
        courses = soup.find_all('div', {'class':'courseblock'})
        for course in courses:
            # basicInfo in the parent of the spans with course info 
            basicInfo = course.find('h3', {'class':'courseblocktitle'})

            # code1 is the prefix, such as AEROSPC and code2 is the actual code, such as 1A
            fullCode = basicInfo.find('span', {'class':'code'}).getText()
            code1 = fullCode[:fullCode.index('\u00a0')].lower()
            code2 = fullCode[fullCode.index('\u00a0') + 1:].lower()

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
            spring  = False
            summer  = False
            
            if "fall 2021" in descriptions[0].lower():
                fall = True
            if "spring 2022" in descriptions[0].lower():
                spring = True
            if "summer 2022" in descriptions[0].lower():
                summer = True
            description = descriptions[1]

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
                        subject = temp[:temp.index('/')].lower()
                        level = temp[temp.index('/') + 1:].lower()
                    # Example: 'Grading/Final exam status: Letter grade. Final exam required.'
                    # grading = 'letter grade' 
                    # final = 'final exam required'
                    elif subHeading == "Grading/Final exam status:":
                        temp = details[i].getText()[len(subHeading) + 1:]
                        grading = temp[:temp.index('.')].lower()
                        final = temp[temp.index('.') + 2:-2].lower()
                    # Example: Grading: Letter grade.
                    # grading = letter grade
                    elif subHeading == "Grading:":
                        grading = details[i].getText()[len(subHeading) + 1:][:-2].lower()
            print(f"fullCode: {fullCode} | code1: {code1} | code2: {code2} | title: {title} | description: {description} | units: {units} | subject: {subject} | level: {level} | fall: {fall} | spring: {spring} | summer: {summer} | grading: {grading} | final: {final}")
            
            cursor.execute("""INSERT IGNORE INTO courses 
                            (fullCode, code1, code2, title, description, units, subject, level, fall, spring, summer, grading, final) 
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                            (fullCode, code1, code2, title, description, units, subject, level, fall, spring, summer, grading, final))
            db.commit()