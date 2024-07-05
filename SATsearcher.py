#Main Script
#Change settings on config.py

import time
import re
import smtplib
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# Import configuration
import config

# Initialize the WebDriver
def initialize_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Optional: if GPU is causing issues
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(executable_path="chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://satsuite.collegeboard.org/sat/test-center-search")
    return driver

# Close the pop-up if present
def close_popup(driver):
    time.sleep(10)
    WebDriverWait(driver, 60).until(
        EC.frame_to_be_available_and_switch_to_it((By.XPATH, "/html/body/div[8]/appcues-container/iframe"))
    )
    time.sleep(5)
    close_button = driver.find_element(By.XPATH, "//*[@id='button-e438cc1d-f5b7-4968-8dde-da9c2cbe7df4']")
    close_button.click()
    driver.switch_to.default_content()

# Perform all the initial settings (testing region, test date, zip code, distance)
def set_up_search(driver, test_date, zip_code, distance):
    # Select the testing region
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "apricot_radio_2"))
    )
    testing_region = driver.find_element(By.ID, "apricot_radio_2")
    testing_region.click()

    # Set the test date
    date_dropdown = Select(driver.find_element(By.ID, "apricot_select_4"))
    time.sleep(2)
    date_dropdown.select_by_visible_text(test_date)

    # Enter the zip code
    zip_enter = driver.find_element(By.ID, "apricot_input_5")
    zip_enter.clear()
    zip_enter.send_keys(zip_code)

    # Select the distance
    distance_dropdown = Select(driver.find_element(By.ID, "apricot_select_6"))
    time.sleep(1)
    distance_dropdown.select_by_visible_text(distance)

# Click the find button and check for results
def find_test_centers(driver):
    find_button = driver.find_element(By.XPATH, "//*[@id='test-center-search']/div[1]/div/div/div/div[2]/button")
    find_button.click()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "no-results"))
        )
        print("No results found. Stopping the script.")
        driver.quit()
        return False
    except:
        return True

# Click available seats and extract the text
def click_available_seats(driver):
    WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@value='available']"))
    )
    available_seats = driver.find_element(By.XPATH, "//*[contains(text(),'Test centers with available seats')]")
    available_seats.click()
    return available_seats.text

# Extract data from the test centers
def extract_test_center_data(driver, number):
    place = driver.find_elements(By.CLASS_NAME, "cb-card-title")
    address_elements = driver.find_elements(By.CLASS_NAME, "cb-card-desc")
    miles_away_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'display-sm-flex')]//p[not(@class)]")

    locations = []
    addresses = []
    miles = []

    for i in range(number):
        try:
            locations.append(place[i].text)
            address_link = address_elements[i].find_element(By.TAG_NAME, "a").get_attribute("href")
            addresses.append(address_link)
            if i < len(miles_away_elements):
                miles.append(miles_away_elements[i].text)
            else:
                miles.append("No miles info")
        except Exception as e:
            print(f"An error occurred at index {i}: {e}")

    return locations, addresses, miles

# Create and send the email
def send_email(locations, addresses, miles, test_date, distance):
    sender = config.sender
    recipient = config.recipient
    password = config.password

    message = EmailMessage()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = "Found a Testing Center"

    # Read the HTML template from the file
    with open("email_template.html", "r") as file:
        html_template = file.read()

    # Replace placeholders in the HTML template with actual data
    test_centers_html = ""
    for loc, addr, mi in zip(locations, addresses, miles):
        test_centers_html += f'''
            <div class="test-center">
                <strong>{loc}</strong><br>
                <a href="{addr}" target="_blank">View on Google Maps</a><br>
                {mi}
            </div>
        '''

    html_body = html_template.format(test_date=test_date, distance=distance, test_centers=test_centers_html)
    message.set_content(html_body, subtype='html')

    # Send the email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(message)
        print("Email sent successfully!")

# Main script execution
def main():
    driver = initialize_driver()
    close_popup(driver)
    
    test_date = config.test_date
    zip_code = config.zip_code
    distance = config.distance

    set_up_search(driver, test_date, zip_code, distance)

    if find_test_centers(driver):
        text = click_available_seats(driver)
        numbers = re.findall(r'\d+', text)
        number = int(numbers[0])
        locations, addresses, miles = extract_test_center_data(driver, number)
        send_email(locations, addresses, miles, test_date, distance)
    driver.quit()

# Run the main function
if __name__ == "__main__":
    main()
