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
    pattern = r'USD \$([\d,]+) - \$([\d,]+)'
    matches = re.findall(pattern, text)
    if matches:
        min_salary, max_salary = [], []
        for match in matches:
            min_salary.append(int(match[0].replace(',', '')))
            max_salary.append(int(match[1].replace(',', '')))
        return min(min_salary), max(max_salary)
    else:
        return ''

driver.get("https://jobs.careers.microsoft.com/global/en/search?l=en_us&pg=1&pgSz=20&o=Relevance&flt=true")

time.sleep(6)

def get_filtered_links(driver):

    
    keywords = ["head", "chief", "president", "vice-president", "vp", "director", "senior-director", "sr. director", "sr-director"]

    while True:
        links_xp = driver.find_elements(By.XPATH, "//button[.='See details']")
        titles_xp = driver.find_elements(By.XPATH,"//div/h2")
        location_xp = driver.find_elements(By.XPATH,"//i[@aria-label='job location icon']/following-sibling::span")
        filtered_links = []
        print(len(links_xp))
        for link,title,location in zip(links_xp,titles_xp,location_xp):
            href = title.text.lower()
            try:
                    location = location.text.split('+')[0].strip()
            except:
                    location = ''
            print(href)
            if any(keyword in href for keyword in keywords):
                data = {
                    "Job_Title": title.text.strip(),
                    "Job_Link": link,
                    "Location": location
                }
                filtered_links.append(data)
        
        extract_inner(filtered_links)
        try:
            next_button = driver.find_element(By.XPATH,"//button[@aria-label='Go to next page']")
            next_button.click()
            time.sleep(4)
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
        company_name = 'Microsoft'
        try:
                job_title = link_data['Job_Title']
        except:
                job_title = ''
        try:
                location = link_data['Location']
        except:
                location = ''
        try:
                salary_range = driver.find_element(By.XPATH,"//h3[.='Qualifications']/following-sibling::div").text.strip()
                salary_range = extract_salary_range(salary_range)
        except:
                salary_range = ''
        try:
                description = driver.find_element(By.XPATH,"//h3[.='Overview']/following-sibling::div").text.strip()          
        except:
                description = ''
        try:
                team_department = driver.find_element(By.XPATH,"//div[.='Discipline']/following-sibling::div").text.strip()
        except:
                team_department = ''
        try:
                date_posted = driver.find_element(By.XPATH,"//div[.='Date posted']/following-sibling::div").text.replace('Posted Date','').replace('" "','').strip()
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
    # extract_inner(links_data)
    driver.close()

main()
