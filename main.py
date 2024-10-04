import os
import re
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.wise-tt.com/wtt_um_feri/"
DOWNLOADS_FOLDER = "/Users/adrianborovnik/Downloads"

def scrape_timetable_ics(url: str) -> None:
    driver = webdriver.Chrome()  # or webdriver.Firefox()
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    program_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt175")))
    program_select.click()

    program_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt175_6")))
    program_option.click()

    time.sleep(1)

    year_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt179")))
    year_select.click()

    year_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt179_3")))
    year_option.click()

    time.sleep(1)

    project_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt183")))
    project_select.click()

    project_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt183_1")))
    project_option.click()

    time.sleep(1)

    week_button = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt241")))
    week_button.click()

    time.sleep(1)
    driver.quit()


def get_file_path(folder_path: str) -> str:
    pattern = r'^calendar(?: \(\d+\))?\.ics$'
    ics_files = [f for f in os.listdir(folder_path) if re.search(pattern, f)]

    if len(ics_files) == 0:
        raise Exception("No valid .ics files found.")

    latest = 0.0
    l_file = ics_files[0]
    for file in ics_files:
        time_c = os.path.getctime(f"{folder_path}/{file}")
        if latest is None or time_c > latest:
            latest = time_c
            l_file = file

    return l_file


def parse_ics(file_path: str):
    pass

def main():
    scrape_timetable_ics(URL)
    file_path = get_file_path(DOWNLOADS_FOLDER)

if __name__ == "__main__":
    main()
