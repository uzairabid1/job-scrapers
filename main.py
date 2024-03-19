import os
import schedule
import time

def run_all_scrapers():
    scrapers_dir = 'companies'    

    scraper_files = os.listdir(scrapers_dir)    

    for file in scraper_files:
        if file.endswith('.py'):
            scraper_path = os.path.join(scrapers_dir, file)
            print(f"Running {file}...")
            os.system(f"python {scraper_path}")

def job():
    print("Starting the scheduled job...")
    run_all_scrapers()
 
schedule.every(24).hours.do(job)


job()

while True:
    schedule.run_pending()
    time.sleep(1)
