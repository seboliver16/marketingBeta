import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

def send_discord_message(webhook_url, message):
    data = {
        "content": message
    }
    requests.post(webhook_url, json=data)

def instaActionsFunction(username, password):

    suspended_url = "https://discord.com/api/webhooks/1169477980045725788/IM2e3GpkGGwXFvvHemH6wSCQ8-UBXFXkhjtsldQp7h7T2RZqXWzUv982B9CbXptc0xjb"
    print("TRYING", username)

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 5)
    couldntFollowCount = 0

    try:
        driver.get('https://www.instagram.com/accounts/login/')
        time.sleep(2)

        username_field = wait.until(EC.visibility_of_element_located((By.NAME, 'username')))
        password_field = wait.until(EC.visibility_of_element_located((By.NAME, 'password')))

        username_field.send_keys(username)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(15)

        df = pd.read_excel(f'{username}.xlsx')
        
        if len(df.loc[df['Contacted'] == False]) > 0:
            users_to_contact = df.loc[df['Contacted'] == False, 'Follower'][:20]

            for user in users_to_contact:
                
                df.loc[df['Follower'] == user, 'Contacted'] = True

                with pd.ExcelWriter(f'{username}.xlsx') as writer:
                    df.to_excel(writer, index=False)

                try:
                    driver.get(f"https://www.instagram.com/{user}")
                    time.sleep(3)
                    follow_button = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.x6s0dn4.x78zum5.x1q0g3np.xs83m0k.xeuugli.x1n2onr6 button._acan._acap._acas._aj1-")))
                    print(user, follow_button.text)
                    if follow_button.text == "Follow":
                        follow_button.click()
                    else:
                        pass
                except:
                    couldntFollowCount += 1
                    print("Could Not Follow")
        if(couldntFollowCount > 15):
            send_discord_message(suspended_url, f"${username} is likely suspended")

        # Load the master account sheet
        master_df = pd.read_excel('masterAccountSheet.xlsx')

        # Calculate the number of users left to contact
        users_left = len(df.loc[df['Contacted'] == False, 'Follower'])

        # Find the row with the corresponding username and update the 'Users Left To Follow' column
        master_df.loc[master_df['Username'] == username, 'Users Left To Follow'] = users_left

        # Save the updated master account sheet
        master_df.to_excel('masterAccountSheet.xlsx', index=False)
        driver.close()

    except Exception as e:
        driver.close()
        print("Could Not Complete Account")