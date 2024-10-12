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

# Extract Issue Keys from a specified cell
def extract_issue_keys(client, spreadsheet_id, sheet_name, row, col):
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet(sheet_name)
    
    # Retrieve cell value from a specified row and column
    cell_value = worksheet.cell(row, col).value

    # Extract issue keys from the parentheses (comma-separated)
    match = re.search(r'\((.*?)\)', cell_value)
    if match:
        issue_keys = match.group(1).split(", ")
        return issue_keys
    else:
        print("Invalid cell format.")
        return []

# Load cities data from JSON
def load_cities(file_path):
    with open(file_path, encoding='utf-8') as file:
        return json.load(file).get("cities_with_two_parts", [])

# بررسی و تنظیم مقدار None برای فیلدهای customfield_20802
def check_marketing_area(issue, valid_cities):
    # گرفتن فیلد مارکتینگ اریا
    marketing_area = getattr(issue.fields, 'customfield_20802', None)  # مارکتینگ اریا

    # اگر مارکتینگ اریا خالی باشد، ایشو نامعتبر است
    if not marketing_area or marketing_area == "None":
        print(f"Issue {issue.key} is invalid because the marketing area is empty.")
        return False

    # بررسی اینکه آیا یکی از شهرهای معتبر در مارکتینگ اریا وجود دارد
    is_valid_city = any(city in marketing_area for city in valid_cities)

    # اگر شهر معتبر باشد، باید حداقل یک خط تیره داشته باشد
    if is_valid_city:
        if '-' in marketing_area:
            print(f"Issue {issue.key} is valid: city is in the valid cities list and contains a hyphen.")
            return True
        else:
            print(f"Issue {issue.key} is invalid: city is in the valid cities list but does not contain a hyphen.")
            return False
    else:
        # اگر هیچ‌کدام از شهرهای معتبر در مارکتینگ اریا نبود، ایشو معتبر است و خط تیره مهم نیست
        print(f"Issue {issue.key} is valid: city is not in the valid cities list, hyphen is not required.")
        return True

def process_issues(jira_client, issue_keys, valid_cities):
    valid_issues = []
    invalid_issues = []

    for key in issue_keys:
        try:
            issue = jira_client.issue(key)
            if check_marketing_area(issue, valid_cities):
                valid_issues.append(key)
            else:
                invalid_issues.append(key)
        except Exception as error:
            print(f"Error retrieving issue {key}: {error}")
            invalid_issues.append(key)

    return valid_issues, invalid_issues

# Define get_cell_value_from_val to save the cell_value
def get_cell_value_from_val():
    # Google Sheets authentication setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    current_directory = Path(__file__).parent
    json_keyfile = current_directory / "json.json"  # فایل اعتبار

    # Authenticate with Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet by ID and worksheet by name
    sheet_id = "1Go5WNUGmiXf0IAiwraAcYoz5NLsNBWEa5tUlDyo22CE"  # ID Sheet
    worksheet_name = "Dashboard"  # نام Worksheet

    # Retrieve the value from a specified cell (row 2, column 98)
    cell_value = client.open_by_key(sheet_id).worksheet(worksheet_name).cell(2, 98).value

    if cell_value:
        return cell_value
    else:
        print("No valid cell value found.")
        return None

# Main processing logic
def handle_issue_processing():
    # Google Sheets setup
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    city_file = Path(__file__).parent / "cities.json"

    # Load cities with two parts
    city_data = load_cities(city_file)

    # Extract cell value using the get_cell_value_from_val function
    cell_value = get_cell_value_from_val()
    if not cell_value:
        return

    # Process the cell_value to extract issue keys
    issue_keys = re.findall(r'SI-\d+', cell_value)
    if not issue_keys:
        print("No valid issue keys found.")
        return

    # Authenticate with Jira
    jira_client = get_jira()

    # Process issue keys and validate marketing areas
    valid_issues, invalid_issues = process_issues(jira_client, issue_keys, city_data)

    # Output results
    if valid_issues:
        valid_keys = ', '.join(valid_issues)
        # اینجا سل ولیو آپدیت میشه
        cell_value = valid_keys
        print(f"Valid issues: {valid_keys}")
    if invalid_issues:
        invalid_keys = ', '.join(invalid_issues)
        print(f"Invalid issues: {invalid_keys}")





