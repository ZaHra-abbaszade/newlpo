import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from jira import JIRA
from utils import get_jira, authenticate_gspread, create_or_get_worksheet, add_issue_to_worksheet, map_month_to_persian
from val_nt import get_cell_value_from_val  # وارد کردن تابع
from datetime import datetime
from persiantools.jdatetime import JalaliDate  # برای ماه شمسی
from pathlib import Path

# Search issues using JQL
def search_issues(jira_client, jql_query, max_results=0):
    try:
        issues = jira_client.search_issues(jql_str=jql_query, maxResults=max_results)
        return issues
    except Exception as e:
        print(f"Error searching issues: {e}")
        return []

# Perform transition on an issue
def perform_transition(jira_client, issue_key, transition_name, fields=None, comment=None):
    try:
        jira_client.transition_issue(issue=issue_key, transition=transition_name, fields=fields, comment=comment)
        print(f"Issue {issue_key} transitioned to {transition_name}.")
    except Exception as e:
        print(f"Error transitioning issue {issue_key}: {e}")

# Main logic to process multiple JQL queries and transition issues
def main():
    jira = get_jira()
    transition_name = "Return Admin Check"  # The transition name or ID to move issues to

    # List to store issue keys and update times
    issue_keys_with_time = []

    # Get the cell value from val_nt.py
    cell_value = get_cell_value_from_val()
    if not cell_value:
        print("No valid cell value found.")
        return

    # Extract only the issue keys from the cell value
    issue_keys = re.findall(r'NVR-\d+', cell_value)
    if not issue_keys:
        print("No valid issue keys found.")
        return

    # Format the issue keys correctly for the JQL query
    issue_keys_str = ', '.join(issue_keys)

    # Manual Assign Date Mapping
    while True:
        custom_month_field_value = input("Enter Manual Assign Date (e.g., aban 1403): ")
        mapped_value = map_month_to_persian(custom_month_field_value)
        if mapped_value:
            custom_month_field_value = mapped_value
            break
        else:
            print("Invalid format! Please enter in the format 'month year' (e.g., aban 1403).")

    # Define multiple JQL queries and their corresponding field updates
    jql_queries_and_updates = [
        {
            "jql": f"issuekey IN ({issue_keys_str}) AND City ~ تهران",
            "fields": {
                "customfield_22631": {"value": "No"},
                "customfield_22632": {"value": "No"},
                "customfield_18602": {"value": "No"},
                "customfield_11003": {"value": "E"},
                "customfield_10804": {"value": "Lead Collection"},
                "customfield_22304": {"value": custom_month_field_value},
                "customfield_11100": {"value": "Tehran"}
            }
        },
        {
            "jql": f"issuekey IN ({issue_keys_str}) AND (City ~ اسلامشهر OR City ~ ورامین OR City ~ 'رباط کریم' OR City ~ پاکدشت OR City ~ قرچک OR City ~ بومهن OR City ~ لواسان OR City ~ رودهن OR City ~ جاجرود OR City ~ پرند OR City ~ دماوند)",
            "fields": {
                "customfield_22631": {"value": "No"},
                "customfield_22632": {"value": "No"},
                "customfield_18602": {"value": "No"},
                "customfield_11003": {"value": "E"},
                "customfield_10804": {"value": "Lead Collection"},
                "customfield_22304": {"value": custom_month_field_value},
                "customfield_11100": {"value": "Other Cities"}
            }
        },
        {
            "jql": f"issuekey IN ({issue_keys_str}) AND (City !~ تهران AND City !~ اسلامشهر AND City !~ ورامین AND City !~ 'رباط کریم' AND City !~ پاکدشت AND City !~ قرچک AND City !~ بومهن AND City !~ لواسان AND City !~ رودهن AND City !~ جاجرود AND City !~ پرند AND City !~ دماوند)",
            "fields": {
                "customfield_22631": {"value": "No"},
                "customfield_22632": {"value": "No"},
                "customfield_18602": {"value": "No"},
                "customfield_11003": {"value": "E"},
                "customfield_10804": {"value": "Lead Collection"},
                "customfield_22304": {"value": custom_month_field_value},
                "customfield_11100": {"value": "Other Cities"}
            }
        }
    ]

    # Loop through each query, search for issues, update fields, and perform the transition
    for query_data in jql_queries_and_updates:
        jql_query = query_data["jql"]
        fields_to_update = query_data["fields"]

        # Search for issues based on the JQL query
        issues = search_issues(jira, jql_query)

        # Perform the field update and transition for each issue found
        for issue in issues:
            issue_key = issue.key
            perform_transition(jira, issue_key, transition_name, fields=fields_to_update, comment="Updated and transitioned by script.")

            update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            issue_keys_with_time.append((issue.key, update_time))

    # Add Google Sheets update if needed
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    current_directory = Path(__file__).parent
    json_keyfile = current_directory / "json.json"
    client = authenticate_gspread(json_keyfile, scope)

    try:
        spreadsheet = client.open('Monthly Update LPO')
        print(f"Spreadsheet 'Monthly Update LPO' already exists.")
    except gspread.exceptions.SpreadsheetNotFound:
        spreadsheet = client.create('Monthly Update LPO')
        print(f"Spreadsheet 'Monthly Update LPO' created.")

    current_month = JalaliDate.today().strftime('%B')
    Not_Touch_worksheet_name = f"Not Touch {current_month}"
    Not_Touch_worksheet = create_or_get_worksheet(spreadsheet, Not_Touch_worksheet_name)

    # Add issue data to worksheet
    add_issue_to_worksheet(Not_Touch_worksheet, issue_keys_with_time)

if __name__ == "__main__":
    main()