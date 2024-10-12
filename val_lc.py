import gspread
from oauth2client.service_account import ServiceAccountCredentials
from jira import JIRA
from consts import HOST, PASSWORD, USERNAME
import re
from pathlib import Path

# Authenticate Google Sheets
def authenticate_gspread(json_keyfile, scope):
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
    client = gspread.authorize(creds)
    return client

# Get Worksheet and Extract Issue Keys
def get_issue_keys_from_worksheet(client, sheet_id, worksheet_name, row, col):
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)
    cell_value = worksheet.cell(row, col).value
    # Use regex to extract values inside parentheses
    issue_keys = re.findall(r'\((.*?)\)', cell_value)
    return issue_keys

# Get Area Data
def get_area_data(client, area_sheet_name, no_area_sheet_name):
    sheet = client.open_by_key("ID_FOR_YOUR_SHEET")
    area_worksheet = sheet.worksheet(area_sheet_name)
    no_area_worksheet = sheet.worksheet(no_area_sheet_name)

    # Read cities from the respective sheets
    area_cities = area_worksheet.col_values(1)  # Assuming cities are in the first column
    no_area_cities = no_area_worksheet.col_values(1)  # Assuming cities are in the first column

    return area_cities, no_area_cities

# Connect to Jira
def get_jira() -> JIRA:
    return JIRA(server=HOST, basic_auth=(USERNAME, PASSWORD))

# Validate issue based on City and Marketing Area
def validate_marketing_area(issue, area_cities, no_area_cities):
    marketing_area = issue.fields.customfield_20802
    city = issue.fields.customfield_10800  

    if city in area_cities:
        # Both parts of the marketing area should be filled
        if marketing_area and hasattr(marketing_area, 'value') and ',' in marketing_area.value:
            part1, part2 = [part.strip() for part in marketing_area.value.split(',')]
            return part1 != "" and part2 != ""
        else:
            return False
    elif city in no_area_cities:
        # Only the first part of the marketing area should be filled
        if marketing_area and hasattr(marketing_area, 'value'):
            part1 = marketing_area.value.split(',')[0].strip()  # Take only the first part
            return part1 != ""
        else:
            return False
    else:
        return False  # Invalid if city is not in either list

# Process Issue Keys
def process_issue_keys(jira, issue_keys, area_cities, no_area_cities):
    valid_issue_keys = []

    for issue_key in issue_keys:
        try:
            issue = jira.issue(issue_key)
            if validate_marketing_area(issue, area_cities, no_area_cities):
                valid_issue_keys.append(issue_key)
                print(f"Issue {issue.key} is valid (Marketing Area filled correctly).")
            else:
                print(f"Issue {issue.key} is invalid (Marketing Area not filled correctly).")
        except Exception as e:
            print(f"Error fetching issue {issue_key}: {e}")

    return valid_issue_keys

# تابع get_cell_value_from_val که سل ولیو را به عنوان خروجی می‌دهد
def get_cell_value_from_val():
    # Google Sheets authentication setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # تنظیم مسیر فایل JSON به صورت نسبی
    current_directory = Path(__file__).parent
    json_keyfile = current_directory / "json.json"

    client = authenticate_gspread(json_keyfile, scope)

    # Get the worksheet and extract issue keys from cell using sheet ID and worksheet name
    sheet_id = "1UIhTjvrmNtP4MkJFV_mYSiu-M1JEFE36MQnhzyc3AkM"
    worksheet_name = "Dashboard"
    issue_keys = get_issue_keys_from_worksheet(client, sheet_id, worksheet_name, 97, 2)

    if not issue_keys:
        print("No issue keys found inside parentheses in the selected cell.")
        return None

    # Load Area and No Area Data from Google Sheets
    area_cities, no_area_cities = get_area_data(client, "area id", "no area id")

    # Connect to Jira
    jira = get_jira()

    # Process the issue keys to find valid ones
    valid_issue_keys = process_issue_keys(jira, issue_keys, area_cities, no_area_cities)

    # Generate the cell value for valid issue keys
    if valid_issue_keys:
        # Create a JQL-compatible string
        cell_value = " , ".join([f"{key}" for key in valid_issue_keys])
        print(f"Valid Issue Keys for JQL Query: {cell_value}")
        return cell_value
    else:
        print("No valid issues found with correctly filled Marketing Area field.")
        return None

# Main function to call in other scripts
if __name__ == "__main__":
    get_cell_value_from_val()




