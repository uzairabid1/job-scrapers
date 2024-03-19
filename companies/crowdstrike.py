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

driver.get("https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers?locationCountry=bc33aa3152ec42d4995f4791a106ed09")

time.sleep(4)

def extract_salary_range(text):
    pattern = r'\$([\d,]+) to \$([\d,]+)'
    matches = re.search(pattern, text)
    if matches:
        min_salary = int(matches.group(1).replace(',', ''))
        max_salary = int(matches.group(2).replace(',', ''))
        return min_salary, max_salary
    else:
        return None


# search_btn = driver.find_element(By.XPATH,"//button[.='Search!']")
# search_btn.click()

def get_filtered_links(driver):

    keywords = ["head", "chief", "president", "vice-president", "vp", "director", "senior director", "sr. Director","senior-director","sr-director"]
    filtered_links = []

    while True:            
        links_xp = driver.find_elements(By.XPATH, "//a[@data-automation-id='jobTitle']")
        for link in links_xp:
            href = link.text.lower()
            if any(keyword in href for keyword in keywords):
                data = {
                    "Job_Title": link.text.strip(),
                    "Job_Link": link.get_attribute('href')
                }
                filtered_links.append(data)
        try:
            next_button = driver.find_element(By.XPATH,"//button[@aria-label='next']")
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
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(2)
            driver.get(job_link)
            time.sleep(4)

            company_name = 'Crowdstrike'
            job_title = link_data['Job_Title']

            try:
                location = driver.find_element(By.XPATH,"//div[@data-automation-id='locations']").text.replace('locations','').strip()
            except:
                location = ''
            try:
                description = driver.find_element(By.XPATH, "//div[@data-automation-id='jobPostingDescription']").text.strip()
                salary_range = extract_salary_range(description)     
            except:
                description = ''
                salary_range = ''

            try:
                team_department = driver.find_element(By.XPATH,"//div[.='Area of Interest']/following-sibling::div").text.strip()
            except:
                team_department = ''
            try:
                date_posted_element = driver.find_element(By.XPATH, "(//div[@data-automation-id='postedOn'])[1]")
                date_posted_text = date_posted_element.text.replace('posted on\n','').strip()
                
                now = datetime.now()

                # Handle different date formats
                if 'Yesterday' in date_posted_text:
                    date_posted = (now - timedelta(days=1)).strftime("%d/%m/%Y")
                elif 'days ago' in date_posted_text or 'Today' in date_posted_text:
                    date_posted = now.strftime("%d/%m/%Y")
                elif '30+ Days Ago' in date_posted_text:
                    # Adjust as needed based on the requirement when '30+ Days Ago' is encountered
                    # Here, assuming it's exactly 30 days ago
                    date_posted = (now - timedelta(days=30)).strftime("%d/%m/%Y")
                else:
                    # Extract number of days from the text and subtract them from current date
                    days_ago = re.search(r'(\d+) Days Ago', date_posted_text)
                    if days_ago:
                        days_ago = int(days_ago.group(1))
                        date_posted = (now - timedelta(days=days_ago)).strftime("%d/%m/%Y")
                    else:
                        date_posted = date_posted_text
            except Exception as e:
                print("Error while parsing date:", e)
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
            driver.close()
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[0])
            driver.switch_to.default_content()


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