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

# گرفتن ماه و سال شمسی فعلی
def get_current_jalali_date():
    current_jalali_datetime = JalaliDatetime.now()
    current_month_name = current_jalali_datetime.strftime('%B')
    current_year = current_jalali_datetime.year
    return f"{current_month_name} {current_year}"


