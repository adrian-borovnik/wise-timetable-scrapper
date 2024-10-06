import os
import re
import time
import datetime as dt

from dotenv import load_dotenv
from google_auth_oauthlib.helpers import credentials_from_session
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

URL = "https://www.wise-tt.com/wtt_um_feri/"
DOWNLOADS_FOLDER = "/Users/adrianborovnik/Downloads"

SCOPES = ["https://www.googleapis.com/auth/calendar"]

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

    # Valid events:
    #   - from now beyond
    #   - lectures (PR) and "vaje" (SV and RV1)
    #   - till sunday (if week option)

    pass


def get_next_sunday_iso() -> str:
    now = dt.datetime.now()
    days_until_sunday = 6 - now.weekday() if now.weekday() <= 6 else 0
    next_sunday = now + dt.timedelta(days=days_until_sunday)
    return next_sunday.isoformat() + "Z"

def get_gcal_creds():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(prot=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

    return creds


def get_events(service, calendar_id: str, week: bool):
    try:
        now = dt.datetime.now().isoformat() + "Z"

        max_date = get_next_sunday_iso() if week == True else None

        event_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=max_date,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = event_result.get("items", [])

        if not events:
            print("No upcoming events found!")
            return None

        return events

        # for event in events:
        #     start = event["start"].get("dateTime", event["start"].get("date"))
        #     print(start, event["summary"])

    except HttpError as error:
        print("An error has occurred:", error)
        return None


def create_event(service, calendar_id = "primary"):
    try:
        event_body = {
            "summary": "Python test event",
            "location": "Online",
            "description": "Awesome event... yolo",
            "colorId": 3,
            "start": {
                "dateTime": "2024-10-06T09:00:00+02:00",
                "timeZone": "Europe/Ljubljana"
            },
            "end": {
                "dateTime": "2024-10-06T14:00:00+02:00",
                "timeZone": "Europe/Ljubljana"
            }
        }

        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()

        print("Event", event)

    except HttpError as error:
        print("An error has occurred while creating an event:", error)


def delete_event(service, calendar_id: str, event_id: str):
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print("Successfully deleted an event")
    except HttpError as error:
        print("An error has occurred while deleting an event:", error)

def main():
    load_dotenv()
    # scrape_timetable_ics(URL)
    # file_path = get_file_path(DOWNLOADS_FOLDER)


    creds = get_gcal_creds()
    service = build("calendar", "v3", credentials=creds)
    # create_event(creds)

    lecture_calendar_id = os.getenv("LECTURE_CALENDAR_ID")
    if lecture_calendar_id is None:
        print("Invalid env variable")
        return

    # events = get_events(service)
    events = get_events(service, lecture_calendar_id, False)
    if events is not None:
        for event in events:
            print(event)

    # delete_event(service, "primary", "vve7atf8111qicf5rmlhbri92o")

if __name__ == "__main__":
    main()


# TODO Add week number option
