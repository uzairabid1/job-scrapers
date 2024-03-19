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


def extract_salary_range(text):
    salary_pattern = re.compile(r'\$([\d,]+)\s*-\s*\$([\d,]+)\s*/year')

    match = salary_pattern.search(text)
    
    if match:
        salary_min = int(match.group(1).replace(',', ''))
        salary_max = int(match.group(2).replace(',', ''))
        return salary_min, salary_max
    else:
        return None

driver.get("https://akamaicareers.inflightcloud.com/search?searchable=%5B%7B%22id%22%3A%22217300106849%22%2C%22text%22%3A%22United%20States%22%2C%22portal%22%3A%228200106849%22%2C%22filterId%22%3A%22LOCATION%22%7D%5D&section=aka_ext")

time.sleep(4)

accept_button = driver.find_element(By.XPATH,"//button[.=' I accept ']")
accept_button.click()
time.sleep(1)

def get_filtered_links(driver):

    keywords = ["head", "chief", "president", "vice-president", "vp", "director", "senior director", "sr. Director","senior-director","sr-director"]
    filtered_links = []

    while True:            
        links_xp = driver.find_elements(By.XPATH, "//div[@aria-labelledby='header-titler']/a")
        dates_xp = driver.find_elements(By.XPATH,"//div[@aria-labelledby='header-postedDate']")
        for link,date in zip(links_xp,dates_xp):
            href = link.text.lower()
            try:
                posted_date = date.text.strip()
            except:
                posted_date = ''
            if any(keyword in href for keyword in keywords):
                data = {
                    "Job_Title": link.text.strip(),
                    "Job_Link": link.get_attribute('href'),
                    "Posted_Date": posted_date
                }
                filtered_links.append(data)
        try:
            next_button = driver.find_element(By.XPATH,"//span[.='Load More']/parent::button")
            next_button.click()
            time.sleep(2)
        except:
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

            company_name = 'Akamai'
            job_title = link_data['Job_Title']

            try:
                location = driver.find_element(By.XPATH,"//label[.='Location']/following-sibling::div").text.strip()
            except:
                location = ''
            try:
                description = driver.find_element(By.XPATH, "//h2[@id='job-description-header']/following-sibling::div").text.strip()
                salary_range = extract_salary_range(description)
            except:
                description = ''
                salary_range = ''

            try:
                team_department = driver.find_element(By.XPATH,"//label[.='Job Field']/following-sibling::div").text.strip()
            except:
                team_department = ''
            try:
                date_posted = link_data["Posted_Date"]
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