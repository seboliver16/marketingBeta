import threading
import time
from datetime import datetime
import pytz
import pandas as pd
from createFollowerList import scrape
from instaActions import instaActionsFunction
from unfollow import unfollowFunction
import os
import logging

# Basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

eastern = pytz.timezone('US/Eastern')
account_semaphore = threading.Semaphore(1)  # Allow up to 4 accounts at a time

instaActions_count = {}
unfollow_count = {}
current_day = datetime.now(eastern).day
processed_accounts_today = {}
# Tracking the last run time for each function for each account
last_run_time = {}  # {account: {'unfollow': datetime, 'instaActions': datetime, 'createFollowerList': datetime}}

def can_run(account, function_name):
    now = datetime.now(eastern)
    if account in last_run_time and function_name in last_run_time[account]:
        time_difference = now - last_run_time[account][function_name]
        if time_difference.total_seconds() < 3600:  # less than an hour
            return False
    if account not in last_run_time:
        last_run_time[account] = {}
    last_run_time[account][function_name] = now
    return True

def unfollowLogic(account, password, blocked):
    global unfollow_count
    global current_day

    now = datetime.now(eastern)
    

    if current_day != now.day:
        unfollow_count.clear()
        instaActions_count.clear()
        current_day = now.day

    if 0 <= now.hour <= 5 and not blocked and unfollow_count.get(account, 0) < 2 and can_run(account, 'unfollow'):
        logging.error(f"Unfollowing for {account}")
        time.sleep(0 * unfollow_count.get(account, 0))  # Consider adjusting this delay based on the specific rate limit requirements
        try:
            unfollowFunction(account, password)
            unfollow_count[account] = unfollow_count.get(account, 0) + 1
        except Exception as e:
            logging.info(f"Unfollow Function for account {account}: {e}")

def instaActionsLogic(account, password, blocked):
    now = datetime.now(eastern)

    if ((now.hour >= 6   and processed_accounts_today[account]["follow"] < 5)) and not blocked and instaActions_count.get(account, 0) < 5 and can_run(account, 'instaActions'):
        if os.path.exists(f"{account}.xlsx"):
            followCount = processed_accounts_today[account]["follow"]
            try:
                instaActionsFunction(account, password)
                processed_accounts_today[account]["follow"] = followCount + 1
            except Exception as e:
                logging.error(f"Error with instaActionsFunction for account {account}: {e}")
            print("sleeping for 3 mins")
            print(datetime.now(eastern))
            time.sleep(210)  # This is to respect Instagram's rate limits


def createFollowerListLogic(account, password, scrapeUser, blocked):
    now = datetime.now(eastern)
    if not os.path.exists(f"{account}.xlsx")  and not blocked and can_run(account, 'createFollowerList'):
        try:
            scrape(account, password, scrapeUser)
        except Exception as e:
            logging.error(f"Error with scrape for account {account}: {e}")
    elif os.path.exists(f"{account}.xlsx"):
        df = pd.read_excel(f"{account}.xlsx")
        not_contacted_count = len(df[df['Contacted'] == False])
        if not_contacted_count <= 100  and not blocked and can_run(account, 'createFollowerList'):
            try:
                scrape(account, password, scrapeUser)
            except Exception as e:
                logging.error(f"Error with scrape for account {account}: {e}")

def process_account(account, password, scrapeUser, blocked):
    try:
        createFollowerListLogic(account, password, scrapeUser, blocked)
        unfollowLogic(account, password, blocked)
        if processed_accounts_today[account]["follow"] < 5:
            instaActionsLogic(account, password, blocked)
        
    except Exception as e:
        logging.error(f"Error processing account {account}: {e}")
    finally:
        account_semaphore.release()

def main():
    while True:
        try:
            accounts_df = pd.read_excel("masterAccountSheet.xlsx")
            now = datetime.now(eastern)
            current_day = now.day
            logging.info(f"Current time: {now}")
            

            if now.hour == 23 and now.minute >= 55:
                for account in processed_accounts_today:
                    processed_accounts_today[account] = { "follow": 0}
                time.sleep(300)  # Sleeping to prevent constant loop without need until the day changes.
                continue

            for index, row in accounts_df.iterrows():
                account = row["Username"]
                password = row["Password"]
                scrapeUser = row["TargetAccount"]
                blocked = row["Blocked"]

                if account not in processed_accounts_today:
                    processed_accounts_today[account] = { "follow": 0}

                if processed_accounts_today[account]["follow"] > 5:
                    
                    continue

                account_semaphore.acquire()
                threading.Thread(target=process_account, args=(account, password, scrapeUser, blocked)).start()

            
            
            time.sleep(60)  # Sleeping for a minute to prevent excessive CPU usage.
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)  # Even in case of an error, sleep for a minute to prevent excessive logs/CPU usage.

if __name__ == "__main__":
    main()