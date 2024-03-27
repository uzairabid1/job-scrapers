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
    pattern = r'\$[\d,]+/year to \$[\d,]+/year'
    matches = re.findall(pattern, text)

    return matches[0] if matches else None

driver.get("https://www.metacareers.com/jobs/?offices[0]=Remote%2C%20US&offices[1]=Menlo%20Park%2C%20CA&offices[2]=Altoona%2C%20IA&offices[3]=Atlanta%2C%20GA&offices[4]=Austin%2C%20TX&offices[5]=Chicago%2C%20IL&offices[6]=Dallas%2C%20TX&offices[7]=Detroit%2C%20MI&offices[8]=Denver%2C%20CO&offices[9]=Forest%20City%2C%20NC&offices[10]=Fort%20Worth%2C%20TX&offices[11]=Henrico%2C%20VA&offices[12]=Huntsville%2C%20AL&offices[13]=Los%20Angeles%2C%20CA&offices[14]=Los%20Lunas%2C%20NM&offices[15]=Miami%2C%20FL&offices[16]=New%20York%2C%20NY&offices[17]=Pittsburgh%2C%20PA&offices[18]=Redmond%2C%20WA&offices[19]=San%20Francisco%2C%20CA&offices[20]=Santa%20Clara%2C%20CA&offices[21]=Fremont%2C%20CA&offices[22]=Irvine%2C%20CA&offices[23]=Washington%2C%20DC&offices[24]=New%20Albany%2C%20OH&offices[25]=Newton%20County%2C%20GA&offices[26]=Seattle%2C%20WA&offices[27]=Sunnyvale%2C%20CA&offices[28]=Sausalito%2C%20CA&offices[29]=Ashburn%2C%20VA&offices[30]=Gallatin%2C%20TN&offices[31]=Reston%2C%20VA&offices[32]=Remote%2C%20US&offices[33]=DeKalb%2C%20IL&offices[34]=Gallatin%2C%20TN&offices[35]=Mesa%2C%20AZ&offices[36]=Kuna%2C%20ID&offices[37]=Kansas%20City%2C%20MO&offices[38]=Burlingame%2C%20CA&offices[39]=Sarpy%20County%2C%20NE&offices[40]=Temple%2C%20TX&offices[41]=Aurora%2C%20IL&offices[42]=Chandler%2C%20AZ&offices[43]=Houston%2C%20TX&offices[44]=Garland%2C%20TX&offices[45]=Sterling%2C%20VA&offices[46]=Valencia%2C%20NM&offices[47]=Stanton%20Springs%2C%20GA&offices[48]=Polk%20County%2C%20IA&offices[49]=Sandston%2C%20VA&offices[50]=Sandston%2C%20VA&offices[51]=Hillsboro%2C%20OR&offices[52]=Crook%20County%2C%20OR&offices[53]=Durham%2C%20NC&offices[54]=San%20Diego%2C%20CA&offices[55]=Vancouver%2C%20WA&offices[56]=Newark%2C%20CA&offices[57]=Jeffersonville%2C%20IN&offices[58]=Eagle%20Mountain%2C%20UT&offices[59]=Utah%20County%2C%20UT&divisions[0]=Facebook")

time.sleep(4)

def get_filtered_links(driver):

    
    keywords = [" director - ","head", "chief", "president", "vice-president", "vp", "director", "senior-director", "sr. director", "sr-director"]
    filtered_links = []

    while True:
        links_xp = driver.find_elements(By.XPATH, "//div[@class='x1ypdohk']")
        titles_xp = driver.find_elements(By.XPATH,"//div[@class='x1ypdohk']/div/div[1]/div[1]")
        team_dept_xp = driver.find_elements(By.XPATH,"//div[@class='x1ypdohk']/div/div[3]/div/div[3]/div")
        print(len(links_xp))
        for link,title,team in zip(links_xp,titles_xp,team_dept_xp):
            href = title.text.lower()
            try:
                    team_dept = team.text.split('+')[0].strip()
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
            next_button = driver.find_element(By.XPATH,"//span[contains(text(),'Load more')]/parent::div/parent::div/parent::div/parent::span/parent::div")
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
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(2)

        job_link = driver.current_url
        company_name = 'Meta'
        try:
                job_title = link_data['Job_Title']
        except:
                job_title = ''
        try:
                location = driver.find_element(By.XPATH,"//span[@class='_8lfp _9a80 _97fe']").text.replace('|','').strip()
        except:
                location = ''
        try:
                salary_range = driver.find_element(By.XPATH,"//div[contains(text(),'/year')]").text.strip()
                salary_range = extract_salary_range(salary_range)
        except:
                salary_range = ''
        try:
                description = driver.find_element(By.XPATH,"//div[@class='_8muv']/div/div[1]").text.strip()          
        except:
                description = ''
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
            # print(data)
        driver.close()
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[0])
        try:
             driver.find_element(By.XPATH,"//span[.='Cancel']/parent::div/parent::div/parent::div/parent::span/parent::div").click()
             time.sleep(2)
        except:
             pass
        


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
