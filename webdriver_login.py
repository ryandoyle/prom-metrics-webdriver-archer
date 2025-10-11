#!/usr/bin/env python3
"""
Selenium WebDriver script to automate login.
Navigates to a URL (from environment variable) and enters a password.
"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def main():
    # Get URL from environment variable
    url = os.getenv('LOGIN_URL')
    
    if not url:
        print("Error: LOGIN_URL environment variable is not set")
        print("Please set it using: export LOGIN_URL='192.168.101.1'")
        sys.exit(1)
    
    # Get password from environment variable
    password = os.getenv('ADMIN_PASS')
    
    if not password:
        print("Error: ADMIN_PASS environment variable is not set")
        print("Please set it using: export ADMIN_PASS='your_password'")
        sys.exit(1)
    
    # Add http:// if not present
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    
    print(f"Navigating to: {url}")
    
    # Initialize the WebDriver with headless Chrome for Docker
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to the URL
        driver.get(url)
        print("Page loaded successfully")
        
        # Wait for the password element to be present (max 10 seconds)
        print("Waiting for password field...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pc-login-password"))
        )
        print("Password field found")
        
        # Enter the password
        password_field.send_keys(password)
        print("Password entered successfully")
        
        # Wait for and click the login button
        print("Waiting for login button...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pc-login-btn"))
        )
        print("Login button found")
        
        login_button.click()
        print("Login button clicked successfully")
        
        # Check for error/warning message after login
        try:
            warning_div = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "grid-warning-msg"))
            )
            # If warning div is found, get the text from the span inside it
            warning_text_span = warning_div.find_element(By.CLASS_NAME, "text")
            warning_message = warning_text_span.text
            print(f"Warning: {warning_message}")
            
            # Click the confirm button to proceed
            print("Waiting for confirm button...")
            confirm_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "confirm-yes"))
            )
            print("Confirm button found")
            confirm_button.click()
            print("Confirm button clicked successfully")
        except TimeoutException:
            # No warning message, continue with the login flow
            print("No warning message detected, continuing...")
        
        # Wait for and click the advanced menu item
        print("Waiting for advanced menu item...")
        advanced_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "advanced"))
        )
        print("Advanced menu item found")
        
        advanced_item.click()
        print("Advanced menu item clicked successfully")
        
        # Get the value from the lteRsrp input element
        print("Waiting for lteRsrp input element...")
        lte_rsrp_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "lteRsrp"))
        )
        print("lteRsrp input element found")
        
        # Wait until the value is not "--"
        print("Waiting for lteRsrp value to update (not '--')...")
        def value_is_not_placeholder(driver):
            element = driver.find_element(By.ID, "lteRsrp")
            value = element.get_attribute("value")
            return value and value != "--"
        
        WebDriverWait(driver, 30).until(value_is_not_placeholder)
        
        lte_rsrp_value = lte_rsrp_input.get_attribute("value")
        print(f"lteRsrp value: {lte_rsrp_value}")
        
        # Get and print additional signal values
        signal_strength_input = driver.find_element(By.ID, "signalStrength")
        signal_strength_value = signal_strength_input.get_attribute("value")
        print(f"signalStrength value: {signal_strength_value}")
        
        lte_rsrq_input = driver.find_element(By.ID, "lteRsrq")
        lte_rsrq_value = lte_rsrq_input.get_attribute("value")
        print(f"lteRsrq value: {lte_rsrq_value}")
        
        lte_snr_input = driver.find_element(By.ID, "lteSnr")
        lte_snr_value = lte_snr_input.get_attribute("value")
        print(f"lteSnr value: {lte_snr_value}")
        
        # In Docker/headless mode, we don't need to wait for user input
        print("Task completed successfully")
        
    # except TimeoutException:
    #     print("Error: Timeout waiting for password field with id 'pc-login-password'")
    #     sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        sys.exit(1)
    finally:
        # Close the browser
        driver.quit()
        print("Browser closed")


if __name__ == "__main__":
    main()
