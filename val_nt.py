import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
from pathlib import Path
from utils import get_jira  # اتصال به Jira

# Authenticate Google Sheets API
def setup_google_sheets(credentials_file, scopes):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scopes)
    return gspread.authorize(credentials)

# Extract Issue Keys from Google Sheets (including keys in parentheses)
def extract_issue_keys(client, spreadsheet_id, sheet_name, row, col):
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet(sheet_name)
    
    # Retrieve cell value from a specified row and column
    cell_value = worksheet.cell(row, col).value
    
    
    # Extract issue keys from inside parentheses (comma-separated)
    match = re.search(r'\((.*?)\)', cell_value)
    if match:
        issue_keys = [key.strip() for key in match.group(1).split(", ")]  # Strip spaces
        return issue_keys
    else:
        print("Invalid cell format or no issues in parentheses.")
        return []

# Load cities data from JSON
def load_cities(file_path):
    with open(file_path, encoding='utf-8') as file:
        return json.load(file).get("cities_with_two_parts", [])

def check_marketing_area(issue, valid_cities):
    # گرفتن فیلد مارکتینگ اریا
    marketing_area = getattr(issue.fields, 'customfield_20802', None)  # مارکتینگ اریا

    if marketing_area is None:
        return False

    # Convert marketing_area to a string if it's not None
    marketing_area_str = str(marketing_area)
    
    # بررسی اینکه آیا یکی از شهرهای معتبر در مارکتینگ اریا وجود دارد
    is_valid_city = any(city in marketing_area_str for city in valid_cities)

    # اگر شهر معتبر باشد، باید حداقل یک خط تیره داشته باشد
    if is_valid_city:
        if '-' in marketing_area_str:
            return True
        else:
            return False
    else:
        # اگر هیچ‌کدام از شهرهای معتبر در مارکتینگ اریا نبود، ایشو معتبر است و خط تیره مهم نیست
        return True

def process_issues(jira_client, issue_keys, valid_cities):
    valid_issues = []
    invalid_issues = []

    for key in issue_keys:
        try:
            issue = jira_client.issue(key)
            if check_marketing_area(issue, valid_cities):
                valid_issues.append(key)  # اگر اوکی بود به لیست ولید اضافه کن
            else:
                invalid_issues.append(key)  # فقط کلید ایشو را به لیست اضافه کن
        except Exception:
            invalid_issues.append(key)  # اگر در پردازش خطایی رخ داد، کلید را به لیست invalid اضافه کن

    return valid_issues, invalid_issues


def handle_issue_processing(username, password):
    # Google Sheets setup
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    city_file = Path(__file__).parent / "cities.json"

    # Load cities with two parts
    city_data = load_cities(city_file)

    # Authenticate Google Sheets
    credentials_file = Path(__file__).parent / "json.json"
    client = setup_google_sheets(credentials_file, scopes)

    # Extract issue keys from Google Sheets (assumed from a specific cell)
    spreadsheet_id = "1Go5WNUGmiXf0IAiwraAcYoz5NLsNBWEa5tUlDyo22CE"
    sheet_name = "Dashboard"
    row, col = 2, 98  # مشخص کردن سلول حاوی issue keys
    issue_keys = extract_issue_keys(client, spreadsheet_id, sheet_name, row, col)

    if not issue_keys:
        print("No valid issue keys found.")
        return None

    # Authenticate with Jira
    jira_client = get_jira(username=username, password=password)  # ارسال username و password

    # Process issue keys and validate marketing areas
    valid_issues, invalid_issues = process_issues(jira_client, issue_keys, city_data)

    # Output results
    cell_value = None  # مقدار اولیه برای cell_value

    if valid_issues:
        valid_keys = ', '.join(valid_issues)  # تبدیل ولید ایشوها به رشته
        cell_value = f"({valid_keys})"  # آپدیت کردن cell_value فقط با کلیدهای معتبر
        print(f"Valid issues: {valid_keys}")

    if invalid_issues:
        invalid_keys = ', '.join(invalid_issues)
        print(f"Invalid issues: {invalid_keys}")  # فقط کلیدهای invalid چاپ می‌شود

    return cell_value  # برگرداندن cell_value در نهایت







