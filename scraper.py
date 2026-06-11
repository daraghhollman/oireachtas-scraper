""""
Script that scrapes text from debates and uploads text alongside metadata to database
"""


# importing packages
from playwright.sync_api import sync_playwright
from tqdm import tqdm
import csv
import sqlite3
import re

#Creating database
connection = sqlite3.connect(r"dail-debates.db")
cursor = connection.cursor()

debate_table = '''create table if not exists debates(
    id integer primary key autoincrement,
    url text,
    title text,
    date DATE,
    text text,
    category text,
    unique (url, id)
)''' 

cursor.execute(debate_table)



#Parsing csv file

with open("debates.csv", "r", encoding="utf-8") as debate_metadata: # opening and reading (the r is for reading) csv file - as debate_csv (naming the variable)
    debate_csv = csv.reader(debate_metadata) # returns object - need to iterate over

    next(debate_csv) # skips first line (as these are our labels)

    debates = [] # List that holds dictionaries for each debate
    for line in debate_csv: # Iterates through each line in csv and creates a dictionary for each 
        if any(line): 
            debate_entry = {
                "title": line[2],
                "date": line[3],
                "url": line[1]
         }
            debates.append(debate_entry) 


#Scrape code 

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True) # Launching Browser (Headless determines whether browser opens)
    page = browser.new_page() #Creating blank new page

    for debate_entry in tqdm(debates, desc=f"Scraping text from debates"):
        page.goto(debate_entry["url"])
        page.wait_for_selector(".questions-answers") #Wait until element with class appears 
        text_elements = page.query_selector_all(".questions-answers") # Finds all elements on page with said html class
    
        text = []
        for element in text_elements:
            element.inner_text()
            text.extend(element.inner_text())

        text = "".join(text)

        debate_entry["text"] = text #Adding text key to each dictionary 
        

    browser.close()

#Importing into sql database

cursor.executemany('''
    insert or ignore into debates(url, title, date, text)
    values(:url, :title, :date, :text)              
''', debates)

cursor.execute("""
               DELETE FROM debates WHERE title LIKE '%Chuaigh an Cathaoirleach Gníomhach%' 
                OR title LIKE '%Chuaigh an Ceann Comhairle i gceannas%'
                OR title LIKE '%Comhaltaí Nua a Chur in Aithne%'
                OR title LIKE '%Message from Select Committee%'                
               """)

cursor.execute("""UPDATE debates SET category = CASE
                WHEN title LIKE '%Order of Business%' THEN 'orderbusiness' 
                WHEN title LIKE '%Business of Dáil%' THEN 'orderbusiness' 
                WHEN title LIKE '%LEADER%' THEN 'leadersq'
                WHEN title LIKE '%Priority Questions%' THEN 'priorityq'
                WHEN title LIKE '%Bill%' THEN 'bills'
                WHEN title LIKE '%topical%' THEN 'topical'
                WHEN title LIKE '%motion%' THEN 'motions'
                WHEN title LIKE '%Questions%' THEN 'otherq'
                ELSE 'other'
               END""")

connection.commit() 
connection.close()


         


