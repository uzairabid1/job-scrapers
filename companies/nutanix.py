from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import os
import pandas as pd
import time
import re
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

options = webdriver.ChromeOptions() 
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--no-sandbox")
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
options.add_argument("--headless=new")

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=options)

def appendProduct(sheet_name, data):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

    gc = gspread.authorize(credentials)

    try:
        sheet = gc.open(sheet_name).sheet1
        if sheet.row_count == 0:
            headers = ["Company","Job Title","Job Link","Date Posted","Found On","Description","Salary Range","Location","Team'/Department"]
            sheet.append_row(headers)
    except Exception as e:
        print(f"An error occurred while opening the Google Sheets document: {str(e)}")
        return False

    try:
        df = pd.DataFrame([data])
        sheet.append_row(df.values.tolist()[0])
    except Exception as e:
        print(f"An error occurred while appending data to the Google Sheets document: {str(e)}")
        return False

    return True


def extract_salary_range(text):
    pattern = r'USD \$([\d,]+) and USD \$([\d,]+) per year'
    matches = re.search(pattern, text)
    if matches:
        min_salary = str(matches.group(1).replace(',', ''))
        max_salary = str(matches.group(2).replace(',', ''))
        return min_salary, max_salary
    else:
        return None

driver.get("https://nutanix.eightfold.ai/careers?location=United%20States%2CUnited%20States")

time.sleep(4)

def get_filtered_links(driver):

    
    keywords = ["head", "chief", "president", "vice-president", "vp", "director", "senior-director", "sr. director", "sr-director"]
    filtered_links = []

    while True:
        links_xp = driver.find_elements(By.XPATH, "//div[@class='card position-card pointer ']")
        titles_xp = driver.find_elements(By.XPATH,"//div[@class='card position-card pointer ']/div[@class='position-title line-clamp line-clamp-2']")
        team_dept_xp = driver.find_elements(By.XPATH,"//div[@class='card position-card pointer ']/div/div")
        print(len(links_xp))
        for link,title,team in zip(links_xp,titles_xp,team_dept_xp):
            href = title.text.lower()
            try:
                    team_dept = team.text.strip()
            except:
                    team_dept = ''
            print(href)
            if any(keyword in href for keyword in keywords):
                data = {
                    "Job_Title": title.text.strip(),
                    "Job_Link": link,
                    "Team/Department": team_dept
                }
                filtered_links.append(data)
        try:
            next_button = driver.find_element(By.XPATH,"//button[.='Show More Positions']")
            next_button.click()
            time.sleep(2)
        except:
            break

    return filtered_links


def extract_inner(links_data):
    for link_data in links_data:
        now = datetime.now()
        found_on = now.strftime("%d/%m/%Y-%H:%M:%S")

        job_button = link_data['Job_Link']
        # driver.get(job_link)
        job_button.click()
        time.sleep(2)

        job_link = driver.current_url
        company_name = 'Nutanix'
        try:
                job_title = link_data['Job_Title']
        except:
                job_title = ''
        try:
                location = driver.find_element(By.XPATH,"//p[@class='position-location']").text.replace('|','').strip()
        except:
                location = ''

        try:
                description = driver.find_element(By.XPATH,"//div[@class='position-job-description truncated-description']").text.strip()          
                salary_range = extract_salary_range(salary_range)
        except:
                description = ''
                salary_range = ''
        try:
                team_department = link_data['Team/Department']
        except:
                team_department = ''
        try:
                date_posted = driver.find_element(By.XPATH,"//span[@class='au-target job-postedDate']").text.replace('Posted Date','').replace('" "','').strip()
        except:
                date_posted = ''

        data = {
                "Company Name": company_name,
                "Job Title": job_title,
                "Job Link": job_link,
                "Date Posted": date_posted,
                "Found On": found_on,
                "Description": description,
                "Salary Range": salary_range,
                "Location": location,
                "Team/Department": team_department
            }
        if not is_link_duplicate('Shaleen-Sheet', job_link):
            appendProduct('Shaleen-Sheet', data)        


def is_link_duplicate(sheet_name, job_link):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(credentials)

    try:

        worksheet = gc.open(sheet_name).sheet1
    except Exception as e:
        print(f"An error occurred while opening the Google Sheets document: {str(e)}")
        return False

    try:
        values_list = worksheet.col_values(3)
        if job_link in values_list:
            return True
    except Exception as e:
        print(f"An error occurred while checking for duplicate link: {str(e)}")
        return False

    return False


def main():

    links_data = get_filtered_links(driver)
    print(links_data)
    extract_inner(links_data)
    driver.close()

main()
