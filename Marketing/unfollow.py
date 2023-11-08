import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openpyxl import Workbook
import pandas as pd
import os
import time
import json
from datetime import datetime, timedelta


def unfollowFunction(account, password):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
           
    driver.get('https://www.instagram.com/accounts/login/')

    time.sleep(2)

            # Log in
    username_field = wait.until(
                EC.visibility_of_element_located((By.NAME, 'username')))
    password_field = wait.until(
                EC.visibility_of_element_located((By.NAME, 'password')))
    username_field.send_keys(account)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    time.sleep(4)
    iterations = 0
    while iterations < 5:  # This will make the function run indefinitely until the condition is met
        try:
            

            driver.get(f"https://www.instagram.com/{account}")
            
            following_count_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'a[href="/{account}/following/"]')))
            following_count = int(following_count_element.text.replace(',', '').split()[0])
            print(account, " is following", following_count, "people")
            if (following_count < 100):
                print(f"{account} is following less than 100 people. Quitting")
                
                driver.quit()
                return

            
            try:
                time.sleep(3)
                following_count_element.click()
       
                
                time.sleep(10)
                buttons = driver.find_elements(By.TAG_NAME, "button")
                count = 0
                for button in buttons:
                    if button.text == "Following":
                        button.click()
                        time.sleep(2)
                        unfollow_buttons = driver.find_elements(By.TAG_NAME, "button")
                        unfollow_button = [b for b in unfollow_buttons if b.text == 'Unfollow'][0]
                        unfollow_button.click()
                        count += 1
                        time.sleep(2)
            except Exception as e:
                print("Could Not Unfollow")
            iterations += 1
        except Exception as e:
            iterations += 1
            error_message = f"Error: {str(e)}"
            print(error_message)