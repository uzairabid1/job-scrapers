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
from datetime import datetime, timedelta
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
    headers = ["Company Name","Job Title","Job Link","Date Posted","Found On","Description","Salary Range","Location","Team/Department"]
    try:
        sheet = gc.open(sheet_name).sheet1
        if sheet.row_count == 0:
            headers = ["Company Name","Job Title","Job Link","Date Posted","Found On","Description","Salary Range","Location","Team/Department"]
            sheet.append_row(headers)
    except Exception as e:
        print(f"An error occurred while opening the Google Sheets document: {str(e)}")
        return False

    try:
        # Convert salary range tuple to string
        salary_range = '-'.join(map(str, data.get('Salary Range', ('', ''))))
        data['Salary Range'] = salary_range

        # Convert data dictionary to list
        data_list = [data.get(key, '') for key in headers]
        sheet.append_row(data_list)
    except Exception as e:
        print(f"An error occurred while appending data to the Google Sheets document: {str(e)}")
        return False

driver.get("https://jobs.apple.com/en-us/search?location=united-states-USA&page=1")
time.sleep(4)


def extract_salary_range(text):
    pattern = r'\$([\d,]+(?:\.\d{2})?)\s+and\s+\$([\d,]+(?:\.\d{2})?)'
    matches = re.search(pattern, text)
    if matches:
        min_salary = int(matches.group(1).replace(',', ''))
        max_salary = int(matches.group(2).replace(',', ''))
        return min_salary, max_salary
    else:
        return '',''


def get_filtered_links(driver):
    keywords = ["head", "chief", "president", "vice-president", "vp", "director", "senior director", "sr. Director","senior-director","sr-director"]
    filtered_links = []

    while True:            
        links_xp = driver.find_elements(By.XPATH, "//a[@class='table--advanced-search__title']")
        print(len(links_xp))
        team_department_xp = driver.find_elements(By.XPATH,"//span[@class='table--advanced-search__role']")
        date_posted_xp = driver.find_elements(By.XPATH,"//span[@class='table--advanced-search__date']")
        for link, team_department, date in zip(links_xp, team_department_xp, date_posted_xp):
            job_title = link.text.strip().lower()
            print(job_title)
            team_department = team_department.text.strip()
            date = date.text.strip()
            if any(re.search(r'\b{}\b'.format(re.escape(keyword)), job_title) for keyword in keywords):
                data = {
                    "Job_Title": link.text.strip(),
                    "Job_Link": link.get_attribute('href'),
                    "Team_Department": team_department,
                    "Date": date
                }
                filtered_links.append(data)
        try:
            next_button = driver.find_element(By.XPATH,"//span[@class='next']/parent::a")
            next_button.click()
        except:
            break
        time.sleep(2)

    return filtered_links


def extract_inner(links_data):
    for link_data in links_data:
        job_link = link_data['Job_Link']
        now = datetime.now()
        found_on = now.strftime("%d/%m/%Y-%H:%M:%S")

        if not is_link_duplicate('Shaleen-Sheet', job_link):
            driver.get(job_link)
            time.sleep(2)

            company_name = 'Apple'
            job_title = link_data['Job_Title']

            try:
                location = driver.find_element(By.XPATH,"//div[@id='job-location-name']").text.replace('Location','').strip()
            except:
                location = ''
            try:   
                salary_range = driver.find_element(By.XPATH,"//div[@aria-controls='acc-pay&benefits']").text.strip()
                salary_range = extract_salary_range(salary_range)
            except:
                salary_range = ''                
            try:
                description = driver.find_element(By.XPATH, "//div[@id='jd-description']").text.strip()
            except:
                description = ''       
            try:
                team_department = links_data["Team_Department"]
            except:
                team_department = ''
            try:
                date_posted = link_data['Date']
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

            print(data)
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