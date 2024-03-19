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

driver.get("https://careers.servicenow.com/careers/jobs?location=United%20States&stretch=10&stretchUnit=MILES&page=1")

time.sleep(2)

accept_btn = driver.find_element(By.CSS_SELECTOR,"button#truste-consent-button")
accept_btn.click()
time.sleep(1)

def get_filtered_links(driver):

    keywords = ["head", "chief", "president", "vice-president", "vp", "director", "senior director", "sr. Director","senior-director","sr-director"]
    filtered_links = []

    pg_idx = 2
    while pg_idx <= 30:            
        links_xp = driver.find_elements(By.XPATH, "//p[@class='job-title']/a")
        for link in links_xp:
            href = link.get_attribute('aria-label').lower()
            if any(keyword in href for keyword in keywords):
                data = {
                    "Job_Title": link.get_attribute('aria-label').strip(),
                    "Job_Link": link.get_attribute('href')
                }
                filtered_links.append(data)
        try:
            driver.get(f"https://careers.servicenow.com/careers/jobs?location=United%20States&stretch=10&stretchUnit=MILES&page={pg_idx}")
            pg_idx+=1
            time.sleep(2)
        except:
            print('meow')
            break

    return filtered_links


def extract_inner(links_data):
    for link_data in links_data:
        job_link = link_data['Job_Link']
        now = datetime.now()
        found_on = now.strftime("%d/%m/%Y-%H:%M:%S")

        if not is_link_duplicate('Shaleen-Sheet', job_link):
            driver.get(job_link)
            time.sleep(2)

            company_name = 'Service Now'
            job_title = link_data['Job_Title']

            try:
                location = driver.find_element(By.XPATH,"//li[@id='header-locations']/span").text.replace('Location','').strip()
            except:
                location = ''
            try:
                description = driver.find_elements(By.XPATH, "//article[@id='description-body']").text.strip()
                description = description[1]

                salary_match = re.search(r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*USD\s*-\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*USD\b', description)
                if salary_match:
                    salary_range = f"{salary_match.group(1)} USD - {salary_match.group(2)} USD"
                else:
                    salary_range = ''     
            except:
                description = ''
                salary_range = ''

            try:
                team_department = driver.find_element(By.XPATH,"//li[@id='header-categories']/span").text.replace('Category','').strip()
            except:
                team_department = ''
            try:
                date_posted = driver.find_element(By.XPATH,"//li[@id='header-posted_date']/span").text.replace('Post Date:').strip()
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
    extract_inner(links_data)
    driver.close()

main()