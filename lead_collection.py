import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from utils import get_jira, authenticate_gspread, create_or_get_worksheet, add_issue_to_worksheet, map_month_to_persian
from val_lc import get_cell_value_from_val
from datetime import datetime
from pathlib import Path

# Function to validate the input format for customfield_22304
def validate_custom_field_input(input_value):
    # Check for Persian months and year in the format "مهر 1403"
    pattern = r"^[\u0600-\u06FF]+\s\d{4}$"
    return bool(re.match(pattern, input_value))

# Search issues using JQL
def search_issues(jira_client, jql_query, max_results=0):
    """
    Use Jira search API to retrieve issues using JQL.
    """
    try:
        issues = jira_client.search_issues(jql_str=jql_query, maxResults=max_results)
        return issues
    except Exception as e:
        print(f"Error searching issues: {e}")
        return []

# Perform a transition on an issue
def perform_transition(jira_client, issue_key, transition_name, fields=None, comment=None):
    """
    Perform a transition on an issue by updating fields and adding optional comments.
    """
    try:
        jira_client.transition_issue(issue=issue_key, transition=transition_name, fields=fields, comment=comment)
        print(f"Issue {issue_key} transitioned to {transition_name}.")
    except Exception as e:
        print(f"Error transitioning issue {issue_key}: {e}")

# Main processing function
def main():
    # Get the cell value from val_lc.py
    cell_value = get_cell_value_from_val()

    if not cell_value:
        print("No valid cell_value found.")
        return

    # Connect to Jira
    jira = get_jira()

    # List to store issue keys and update times
    issue_keys_with_time = []

    # Get input from user for customfield_22304 with month mapping
    while True:
        custom_month_field_value = input("Enter Manual Assign Date (e.g., aban 1403): ")
        mapped_value = map_month_to_persian(custom_month_field_value)
        if mapped_value:
            custom_month_field_value = mapped_value
            break
        else:
            print("Invalid format! Please enter in the format 'month year' (e.g., aban 1403).")

    # Extract issue keys
    issue_keys = re.findall(r'NVR-\d+', cell_value)
    if not issue_keys:
        print("No valid issue keys found.")
        return

    issue_keys_str = ', '.join(issue_keys)

    # Define multiple JQL queries and field updates
    jql_queries_and_updates = [
        {
            "jql": f"issuekey IN ({issue_keys_str}) AND City ~ تهران AND status != 'LC Pool'",
            "fields": {
                "customfield_22631": {"value": "No"},
                "customfield_22632": {"value": "No"},
                "customfield_18602": {"value": "No"},
                "customfield_11003": {"value": "E"},
                "customfield_10804": {"value": "Lead Collection"},
                "customfield_22304": {"value": custom_month_field_value},
                "customfield_14314": {"value": "Tehran Sales"},
                "customfield_11100": {"value": "Tehran"}
            }
        },
        {
            "jql": f"issuekey IN ({issue_keys_str}) AND (City ~ اسلامشهر OR City ~ ورامین OR City ~ 'رباط کریم' OR City ~ پاکدشت OR City ~ قرچک OR City ~ بومهن OR City ~ لواسان OR City ~ رودهن OR City ~ جاجرود OR City ~ پرند OR City ~ دماوند) AND status != 'LC Pool'",
            "fields": {
                "customfield_22631": {"value": "No"},
                "customfield_22632": {"value": "No"},
                "customfield_18602": {"value": "No"},
                "customfield_11003": {"value": "E"},
                "customfield_10804": {"value": "Lead Collection"},
                "customfield_22304": {"value": custom_month_field_value},
                "customfield_14314": {"value": "Tehran Sales"},
                "customfield_11100": {"value": "Other Cities"}
            }
        },
        {
            "jql": f"issuekey IN ({issue_keys_str}) AND (City !~ تهران AND City !~ اسلامشهر AND City !~ ورامین AND City !~ 'رباط کریم' AND City !~ پاکدشت AND City !~ قرچک AND City !~ بومهن AND City !~ لواسان AND City !~ رودهن AND City !~ جاجرود AND City !~ پرند AND City !~ دماوند) AND status != 'LC Pool'",
            "fields": {
                "customfield_22631": {"value": "No"},
                "customfield_22632": {"value": "No"},
                "customfield_18602": {"value": "No"},
                "customfield_11003": {"value": "E"},
                "customfield_10804": {"value": "Lead Collection"},
                "customfield_22304": {"value": custom_month_field_value},
                "customfield_14314": {"value": "Other Cities Sales"},
                "customfield_11100": {"value": "Other Cities"}
            }
        }
    ]

    # First, transition all issues not already in "LC Pool"
    for query_data in jql_queries_and_updates:
        jql_query = query_data["jql"]
        fields_to_update = query_data["fields"]

        # Search for issues based on the JQL query
        issues = search_issues(jira, jql_query)

        # Perform the field update and transition for each issue found to "LC Pool"
        for issue in issues:
            issue_key = issue.key
            perform_transition(jira, issue_key, "LC Pool", fields=fields_to_update, comment="Updated and transitioned to LC Pool by script.")
            issue_keys_with_time.append((issue_key, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    # After all issues are transitioned to "LC Pool", now transition ALL issues to "NVR Linked Issue"
    jql_query = f"issuekey IN ({issue_keys_str})"
    issues = search_issues(jira, jql_query)

    for issue in issues:
        issue_key = issue.key
        perform_transition(jira, issue_key, "NVR Linked Issue", comment="Transitioned to NVR Linked Issue by script.")
        issue_keys_with_time.append((issue_key, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    # Connect to Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    current_directory = Path(__file__).parent
    json_keyfile = current_directory / "json.json"

    client = authenticate_gspread(json_keyfile, scope)

    # Create or open the spreadsheet
    try:
        spreadsheet = client.open('Monthly Update LPO')
        print(f"Spreadsheet 'Monthly Update LPO' already exists.")
    except gspread.exceptions.SpreadsheetNotFound:
        spreadsheet = client.create('Monthly Update LPO')
        print(f"Spreadsheet 'Monthly Update LPO' created.")

    # Create or open the worksheet for Lead Collection updates
    lead_collection_worksheet_name = f"Lead Collection {custom_month_field_value}"
    lead_collection_worksheet = create_or_get_worksheet(spreadsheet, lead_collection_worksheet_name)

    # Add issue data to the worksheet
    add_issue_to_worksheet(lead_collection_worksheet, issue_keys_with_time)

if __name__ == "__main__":
    main()
