import gspread
from oauth2client.service_account import ServiceAccountCredentials
from jira import JIRA
from datetime import datetime
from khayyam import JalaliDatetime
from pathlib import Path

# Set your Jira host manually
HOST = 'https://jira.snappfood.ir'  # Manually set the Jira host

# اتصال به Jira
def get_jira() -> JIRA:
    # Requesting username and password as input
    username = input("Enter your Jira username: ")
    password = input("Enter your Jira password: ")
    return JIRA(server=HOST, basic_auth=(username, password))

# احراز هویت Google Sheets
def authenticate_gspread(json_keyfile, scope):
    creds = ServiceAccountCredentials.from_json_keyfile_name(str(json_keyfile), scope)
    client = gspread.authorize(creds)
    return client

# ایجاد یا باز کردن یک worksheet با نام مشخص
def create_or_get_worksheet(spreadsheet, worksheet_name):
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        print(f"Worksheet '{worksheet_name}' already exists.")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols="2")
        worksheet.append_row(["Issue Key", "Update Time"])
        print(f"Worksheet '{worksheet_name}' created.")
    return worksheet

# افزودن اطلاعات به worksheet
def add_issue_to_worksheet(worksheet, issue_keys_with_time):
    for issue_key, update_time in issue_keys_with_time:
        worksheet.append_row([issue_key, update_time])

# Mapping for English month names to Persian equivalents
english_to_persian_months = {
    "farvardin": "فروردین",
    "ordibehesht": "اردیبهشت",
    "khordad": "خرداد",
    "tir": "تیر",
    "mordad": "مرداد",
    "shahrivar": "شهریور",
    "mehr": "مهر",
    "aban": "آبان",
    "azar": "آذر",
    "dey": "دی",
    "bahman": "بهمن",
    "esfand": "اسفند"
}

# Function to map English month names to Persian equivalents
def map_english_to_persian(input_value):
    month, year = input_value.split()
    if month.lower() in english_to_persian_months:
        return f"{english_to_persian_months[month.lower()]} {year}"
    else:
        return None

