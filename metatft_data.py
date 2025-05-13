from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Initialize the WebDriver (make sure to replace 'path_to_chromedriver' with the actual path)
driver = webdriver.Chrome(executable_path="path_to_chromedriver")

try:
    # Navigate to the MetaTFT player page
    url = "https://www.metatft.com/player/tw/%E6%B5%AA%E6%BC%AB%E5%88%9D%E5%A4%9C-tw2"
    driver.get(url)

    # Wait for the page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Locate and click the expand button (adjust the selector as needed)
    expand_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Expand')]"))
    )
    expand_button.click()

    # Wait for the content to load
    time.sleep(3)  # Adjust the sleep time as needed

    # Extract the data (adjust the selector to target the desired content)
    matches = driver.find_elements(By.CLASS_NAME, "match-class-name")  # Replace with the actual class name
    for match in matches:
        print(match.text)

finally:
    # Close the browser
    driver.quit()