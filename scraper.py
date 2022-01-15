# TODO
# Get links using bs4 instead of Selenium 

from selenium import webdriver
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

from time import sleep
import requests

from dotenv import load_dotenv

# The indices are NOT 0 indexed, they are 1 indexed instead 
COURSE_ALPHA =  "//div[@id='atozindex']/ul"
COURSE_CATEGORIES = "./li/a"
COURSE_HEADER = "../h2[{index}]"

EXPAND_BTN = "//button[@class='btn_expandAll]"
COURSE = "//div[@class='courseblock]"

# Open Nextdoor
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
            code = basicInfo.find('span', {'class':'code'}).getText()
            code1 = code[:code.index('\u00a0')]
            code2 = code[code.index('\u00a0') + 1:]

            # title is not processed 
            title = basicInfo.find('span', {'class':'title'}).getText()

            # units is stripped of text to become an integer 
            units = basicInfo.find('span', {'class':'hours'}).getText()
            units = units[:units.index(' ')]

            # details has more advanced info such as prereqs 
            sections = course.find('div', {'class':'coursedetails'}).findChildren('div', recursive=False)
            for section in sections:
                details = section.findChildren('p', recursive=False)
                heading = details[0].getText
                for i in range(1, len(details)):
                    subHeading = details[i].find('strong').getText()
                    text = details[i].getText()
                    print(text)



