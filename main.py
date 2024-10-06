import os
import re
import time
import datetime as dt

from dotenv import load_dotenv
from google_auth_oauthlib.helpers import credentials_from_session
from googleapiclient.http import BatchHttpRequest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pathlib import Path
from ical.calendar_stream import IcsCalendarStream
from ical.exceptions import CalendarParseError
from ical.event import Event

URL = "https://www.wise-tt.com/wtt_um_feri/"
DOWNLOADS_FOLDER = "/Users/adrianborovnik/Downloads"

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class ScrapeConfig:
    def __init__(self, url: str, whole_calendar: bool = False, week_num: int | None = None):
        self.url = url
        self.whole_calendar = whole_calendar

        academic_week_num = None
        if whole_calendar is False and week_num:
            academic_week_num = (week_num - 39) % 52 or 52

        self.academic_week_num = academic_week_num


def scrape_timetable_ics(config: ScrapeConfig) -> None:
    # TODO Make this more robust to id changing

    driver = webdriver.Chrome()  # or webdriver.Firefox()
    driver.get(config.url)

    wait = WebDriverWait(driver, 10)

    program_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt186")))
    program_select.click()

    program_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt186_6")))
    program_option.click()

    time.sleep(1)

    year_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt191")))
    year_select.click()

    year_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt191_3")))
    year_option.click()

    time.sleep(1)

    project_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt197")))
    project_select.click()

    project_option = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt197_1")))
    project_option.click()

    time.sleep(1)

    if not config.whole_calendar and config.academic_week_num:
        week_select = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt158")))
        week_select.click()

        week_option = wait.until(EC.visibility_of_element_located((By.ID, f"form:j_idt158_{config.academic_week_num - 1}")))
        week_option.click()

        time.sleep(1)

    if config.whole_calendar:
        whole_button = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt260")))
        whole_button.click()
    else:
        week_button = wait.until(EC.visibility_of_element_located((By.ID, "form:j_idt256")))
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

    return f"{folder_path}/{l_file}"


class ParseConfig:
    def __init__(self, file_path: str):
        self.file_path = file_path


def parse_ics(config: ParseConfig):

    # Valid events:
    #   - from now beyond
    #   - lectures (PR) and "vaje" (SV and RV 1)
    #   - till sunday (if week option)

    all_events = None

    filename = Path(config.file_path)
    with filename.open() as ics_file:
        try:
            calendar = IcsCalendarStream.calendar_from_ics(ics_file.read())
            all_events = [event for event in calendar.timeline]
        except CalendarParseError as err:
            print(f"Failed to parse ics file '{str(filename)}': {err}")


    if all_events is None:
        print("No valid events!")
        return []

    lecture_pattern = r'PR'
    exercise_pattern = r"(SV|RV 1)"
    today = dt.datetime.today()

    lecture_events = []
    exercise_events = []

    for event in all_events:
        if event.dtstart < today:
            continue

        if re.search(lecture_pattern, event.description):
            lecture_events.append(event)
            continue

        if re.search(exercise_pattern, event.description):
            exercise_events.append(event)

    return lecture_events, exercise_events


def get_next_sunday_iso() -> str:
    now = dt.datetime.now()
    days_until_sunday = 6 - now.weekday() if now.weekday() <= 6 else 0
    next_sunday = now + dt.timedelta(days=days_until_sunday)
    return next_sunday.isoformat() + "Z"

def get_monday_of_week(year: int, week_num: int) -> dt.datetime:
    first_day_of_year = dt.datetime(year, 1, 1)
    first_week_monday = first_day_of_year - dt.timedelta(days=first_day_of_year.weekday())
    monday_of_week = first_week_monday + dt.timedelta(weeks=week_num - 1)

    return monday_of_week

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


def get_events(service, calendar_id: str, week_num: int | None = None):

    # TODO validate week so that is not before today

    try:
        today = dt.datetime.today()
        time_min = today
        time_max = None

        if week_num:
            time_min = get_monday_of_week(today.year, week_num)
            time_max = time_min + dt.timedelta(days=6)

        event_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat() + "Z",
            timeMax=time_max.isoformat() + "Z" if time_max is not None else None,
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


def create_event(service, calendar_id, event: Event):
    try:
        event_body = {
            "summary": event.summary,
            "location": event.location,
            "description": event.description,
            "start": {
                "dateTime": event.dtstart.isoformat(),
                "timeZone": "Europe/Ljubljana"
            },
            "end": {
                "dateTime": event.dtend.isoformat(),
                "timeZone": "Europe/Ljubljana"
            }
        }

        gcal_event = service.events().insert(calendarId=calendar_id, body=event_body).execute()

        print("Event", gcal_event)

    except HttpError as error:
        print("An error has occurred while creating an event:", error)


def delete_event(service, calendar_id: str, event_id: str):
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except HttpError as error:
        print("An error has occurred while deleting an event:", error)


def delete_events_from_today_onwards(service, calendar_id: str):
    event_result = service.events().list(
        calendarId=calendar_id,
        timeMin=dt.datetime.today().isoformat() + "Z",
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = event_result.get("items", [])

    if not events:
        return

    for event in events:
        delete_event(service, calendar_id, event["id"])



def main():
    load_dotenv()

    scrape_timetable_ics(ScrapeConfig(URL, True))
    file_path = get_file_path(DOWNLOADS_FOLDER)

    (l_events, e_events) = parse_ics(ParseConfig(file_path))

    creds = get_gcal_creds()
    service = build("calendar", "v3", credentials=creds)


    lecture_gcal_id = os.getenv("LECTURE_CALENDAR_ID")
    if lecture_gcal_id is None:
        print("Invalid env variable")
        return

    exercise_gcal_id = os.getenv("EXERCISE_CALENDAR_ID")
    if exercise_gcal_id is None:
        print("Invalid env variable")
        return

    gcal_lecture_events = get_events(service, lecture_gcal_id)
    if gcal_lecture_events is not None:
        for event in gcal_lecture_events:
            print(event["id"])

    gcal_exercise_events = get_events(service, exercise_gcal_id, 40)
    if gcal_exercise_events is not None:
        for event in gcal_exercise_events:
            print(event)

    # delete_events_from_today_onwards(service, lecture_gcal_id)

    # TODO parallelization

    for event in l_events:
        create_event(service, lecture_gcal_id, event)


    for event in e_events:
        create_event(service, exercise_gcal_id, event)



if __name__ == "__main__":
    main()
