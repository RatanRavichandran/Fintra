from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time

options = webdriver.ChromeOptions()
prefs = {
    "download.prompt_for_download": False,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)
actions = ActionChains(driver)

driver.get("https://www.amfiindia.com/research-information/other-data/mf-scheme-performance-details")

# Step 1: Wait for iframe and switch to it
def switch_to_iframe():
    try:
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe")))
        print("[OK] Switched to iframe")
    except Exception as e:
        print("[X] Failed to switch to iframe:", str(e))

# Step 2: Close popup if exists
def close_popup():
    try:
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "cdk-overlay-pane")))
        driver.execute_script("""
            let popup = document.querySelector('.cdk-overlay-container');
            if (popup) popup.remove();
        """)
        print("[OK] Popup closed")
    except:
        print("[INFO] No popup appeared")

# Step 3: Set date
def set_date():
    try:
        date_value = (datetime.today() - timedelta(days=2)).strftime('%d-%b-%Y')
        date_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[bsdatepicker]")))
        driver.execute_script("arguments[0].removeAttribute('readonly')", date_input)
        date_input.clear()
        date_input.send_keys(date_value)
        print("[OK] Date set:", date_value)
    except Exception as e:
        print("[X] Date picker failed:", str(e))

# Step 4: Click Go button
def click_go():
    try:
        go_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Go')]]")))
        actions.move_to_element(go_btn).click().perform()
        print("[OK] Clicked Go")
    except Exception as e:
        print("[X] Couldn't click Go:", str(e))

# Step 5: Click Excel Download
def click_excel():
    try:
        time.sleep(3)
        excel_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'excel-border')]")))
        actions.move_to_element(excel_btn).click().perform()
        print("[OK] Excel download clicked")
    except Exception as e:
        print("[X] Excel download failed:", str(e))

# Flow
switch_to_iframe()
close_popup()
set_date()
click_go()
click_excel()

time.sleep(5)
driver.quit()
