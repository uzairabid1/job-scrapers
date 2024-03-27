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
from selenium.webdriver.common.action_chains import ActionChains
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

driver.get("https://jobs.juniper.net/careers?location=united%20states")

time.sleep(8)
# input_field = driver.find_element(By.XPATH,"//input[@aria-label='Filter position by Location']")
# input_field.send_keys("United States")
# time.sleep(2)
# input_field.send_keys(Keys.ENTER)
# time.sleep(5)


def extract_salary_range(text):
    # Regular expression to extract salary range
    salary_pattern = re.compile(r'\$\d{1,3}(?:,\d{3})*\.\d{2}')

    # Find all occurrences of salary pattern in the text
    salaries = salary_pattern.findall(text)

    # Extracting the minimum and maximum salaries
    if len(salaries) >= 2:
        salary_min = int(salaries[0].replace('$', '').replace(',', ''))
        salary_max = int(salaries[1].replace('$', '').replace(',', ''))
        return salary_min, salary_max
    else:
        return ''


# search_btn = driver.find_element(By.XPATH,"//button[.='Search!']")
# search_btn.click()

def get_filtered_links(driver):

    keywords = ["head", "chief", "president", "vice-president", "vp", "director", "senior director", "sr. Director","senior-director","sr-director"]
    

    while True:            
        links_xp = driver.find_elements(By.XPATH, "//div[@class='card position-card pointer ']")
        locations_xp = driver.find_elements(By.XPATH,"//p[@class='position-location line-clamp line-clamp-2 body-text-2 p-up-margin']")
        filtered_links = []
        print(len(links_xp))
        for link,location in zip(links_xp,locations_xp):
            href = link.text.lower()
            if any(keyword in href for keyword in keywords):
                location_text = location.text.strip()
                upd_location = location_text.split(' and ')[0] if ' and ' in location_text else location_text
                data = {
                    "Job_Title": link.text.strip(),
                    "Job_Link": link,
                    "Location": upd_location,
                }
                filtered_links.append(data)
        try:
            scrollable_container=driver.find_element(By.XPATH,"//div[@class='position-sidebar-scroll-handler  ']")
            driver.execute_script("arguments[0].scrollBy(0, 500);", scrollable_container)
            time.sleep(3)
            show_more = driver.find_element(By.XPATH,"//button[.='Show More Positions']")
            show_more.click()
        except:
            print("done")
            break
        time.sleep(2)

    return filtered_links


def extract_inner(links_data):
    
    for link_data in links_data:
        job_link = link_data['Job_Link']
        job_title = link_data['Job_Title']
        now = datetime.now()
        found_on = now.strftime("%d/%m/%Y-%H:%M:%S")

        if not is_title_duplicate('Shaleen-Sheet', job_title):
            driver.execute_script("arguments[0].scrollIntoView();", job_link)
            time.sleep(3)
            wait = WebDriverWait(driver, 10)
            driver.execute_script("window.scrollTo(0,0);")
            time.sleep(2)
            
            prev_sibling = driver.execute_script("return arguments[0].previousElementSibling;", job_link)
            driver.execute_script("arguments[0].classList.add('card-selected');", job_link)
            time.sleep(3)
            driver.execute_script("arguments[0].click();", job_link)
            time.sleep(2)
            
            url=driver.current_url
            company_name = 'Juniper'
            location = link_data['Location']

            try:
                description_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='position-job-description']")))
                description = description_element.text.strip()
                salary_range = extract_salary_range(description)
            except Exception as e:
                print(f"Error extracting description: {e}")
                description = ''
                salary_range = ''

            try:
                team_department = driver.find_element(By.XPATH,"//div[.='Area of Interest']/following-sibling::div").text.strip()
            except:
                team_department = ''
            try:
                date_posted = driver.find_element(By.XPATH,"(//div[@data-automation-id='postedOn'])[1]").text.strip()
                
            except:
                date_posted = ''

            data = {
                "Company Name": company_name,
                "Job Title": job_title,
                "Job Link": url,
                "Date Posted": date_posted,
                "Found On": found_on,
                "Description": description,
                "Salary Range": salary_range,
                "Location": location,
                "Team/Department": team_department
            }

            print(data)
            appendProduct('Shaleen-Sheet', data)
            
            


def is_title_duplicate(sheet_name, job_title):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(credentials)

    try:

        worksheet = gc.open(sheet_name).sheet1
    except Exception as e:
        print(f"An error occurred while opening the Google Sheets document: {str(e)}")
        return False

    try:
        values_list = worksheet.col_values(2)
        if job_title in values_list:
            return True
    except Exception as e:
        print(f"An error occurred while checking for duplicate title: {str(e)}")
        return False

    return False


def main():

    links_data = get_filtered_links(driver)
    print(links_data)
    extract_inner(links_data)
    driver.close()

main()