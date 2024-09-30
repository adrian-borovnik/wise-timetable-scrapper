import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.wise-tt.com/wtt_um_feri/"

def scrape_timetable(url: str) -> None:

    driver = webdriver.Chrome()  # or webdriver.Firefox()
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    program_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt179")))
    program_select.click()

    program_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt179_6")))
    program_option.click()

    time.sleep(1)

    year_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt183")))
    year_select.click()

    year_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt183_3")))
    year_option.click()

    time.sleep(1)

    project_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt187")))
    project_select.click()

    project_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt187_1")))
    project_option.click()

    time.sleep(1)

    week_button = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt250")))
    week_button.click()

    time.sleep(3)
    driver.quit()

def get_file_path(folder_path: str):
    pass

def parse_ics():
    pass

def main():
    scrape_timetable(URL)

if __name__ == "__main__":
    main()
