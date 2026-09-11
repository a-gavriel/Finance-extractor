"""
Finance-Tracker goes through a given user's gmail inbox to parse a group of emails to identify
different bank transactions, extract their metadata, classify and tabulate them.
"""

import os.path
import base64
import time
import traceback
import sys
from enum import Enum
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from select_calendar import select_date

from exporter import export_to_xlsx
from banks import BANK_PROCESSORS
from models.email import Email
from models.transaction import Transaction

DATETIME_FORMATER = "%Y/%m/%d"

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]


class OperationMode(Enum):
    NONE = 0
    GUI = 1
    DEV = 2
    MANUAL = 3


def define_query(operation_mode: int) -> tuple[int, str]:
    """
    Defines the query to be used to search for bank emails. Depending on the operation mode.

    Modes:
    - GUI    : Displays a calendar to select start and end dates to search
    - DEV    : Searches for emails within the last 30 days
    - Manual : Asks the user to manually write a search query to search the desired emails

    Note: In GUI and DEV mode filters using the label 'Bancos'
    """
    if operation_mode == OperationMode.GUI:
        print("Using Script in GUI mode")
        selected_date = []
        select_date(selected_date)
        if selected_date:
            result = (
                300,
                f"label:Bancos after:{selected_date[0]}  before:{selected_date[1]}",
            )
            print(f"Search Query:\n - limit={result[0]}\n - query={result[1]}")
            return result

    if operation_mode == OperationMode.MANUAL:
        print("Using Script in Manual mode")
        while True:
            result = define_query_manually()
            print("\n----------------------")
            print(
                f"Selected options:\n  max results:\t{result[0]}\n  query:\t{result[1]}"
            )
            print("\n----------------------\n")
            resume = input("Continue (y/n):").lower().strip()
            if resume[0] == "y":
                print("")
                break
        return result

    if operation_mode == OperationMode.DEV:
        # Default options are:
        #       results: 300
        #       query: "label:Bancos after:YYYY/MM/DD"
        print("Using Script in DEV mode")
        today = datetime.today()
        start_date = today - timedelta(days=30)
        start_date_str = start_date.strftime(DATETIME_FORMATER)
        result = 300, f"label:Bancos after:{start_date_str}"
        print(f"Search Query:\n - limit={result[0]}\n - query={result[1]}")
        return result


def define_query_manually() -> tuple[int, str]:
    """
    Asks the users to input a custom search query to identify the desired emails
    """
    max_results: int = 100
    while True:
        try:
            max_results = int(input("Max results [max=500]:").strip())
            if max_results < 1 or max_results > 500:
                raise ValueError("Must be between 1 and 500")
            else:
                break
        except Exception:
            print("Invalid input. Please try again!")

    print(
        "\nPlease input the search query to use."
        "\nTake into consideration that the search by date uses the timezone of UTC"
        "\nExample: 'label:Bancos from:AlertasScotiabank@scotiabank.com  after:2024/04/16'"
        "\n - Bank emails: notificacion@notificacionesbaccr.com , AlertasScotiabank@scotiabank.com , bcrtarjestcta@bancobcr.com"
        "\n\nCheck https://support.google.com/mail/answer/7190?hl=en on how to make a search query."
    )
    query = input("\n\nSearch query:\n>>> ")

    return (max_results, query)


def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if os.path.exists("token.json"):
            os.remove("token.json")
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_messages(service, operation_mode):
    """Request a list of all the messages"""
    # messages is a list of dictionaries where each dictionary contains a message id.
    max_emails, search_query = define_query(operation_mode)
    result = (
        service.users()
        .messages()
        .list(maxResults=max_emails, userId="me", q=search_query)
        .execute()
    )
    messages = result.get("messages")
    return messages


def process_email(email: Email, processed_transactions: list[Transaction]) -> bool:
    try:
        for processor in BANK_PROCESSORS:
            if processor.identify(email):
                transaction = processor.process(email)
                if transaction:
                    processed_transactions.append(transaction)
                return True
        return False
    except Exception as e:
        print(f"Error processing email. Skiping email: {email}. Error: {e}")
        return False


def process_messages(
    service,
    transactions_to_export: list[Email],
    messages: dict,
    operation_mode: OperationMode,
):
    messages_len = len(messages)
    print("Found", messages_len, "messages that match the search query\n")
    # messages is a list of dictionaries where each dictionary contains a message id.
    # iterate through all the messages
    for i, msg in enumerate(messages):
        print(f"Parsing emails: {i+1}/{messages_len}", end="\r", flush=True)
        # Get the message from its id
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()

        headers = msg_data["payload"]["headers"]
        current_email = Email()
        # Look for Subject and Sender Email in the headers
        for d in headers:
            if d["name"] == "Subject":
                current_email.subject = d["value"]
            if d["name"] == "From":
                current_email.sender = d["value"]
            if d["name"] == "X-Received":
                current_email.date_str = d["value"]
                current_email.date_str = current_email.date_str[
                    current_email.date_str.rfind(";") + 1 :
                ].strip()
                current_email.date_str = current_email.date_str[
                    : current_email.date_str.rfind("(")
                ].strip()

        current_email.body = "Not decrypted"

        try:
            # The Body of the message is in Encrypted format. So, we have to decode it.
            # Get the data and decode it with base 64 decoder.
            encoded_body = ""
            if msg_data["payload"]["body"]["size"] > 0:
                encoded_body = msg_data["payload"]["body"]["data"]
            elif len(msg_data["payload"]["parts"]) > 0:
                part_no = 0
                if msg_data["payload"]["parts"][0]["mimeType"] == "text/html":
                    part_no = 0
                elif msg_data["payload"]["parts"][1]["mimeType"] == "text/html":
                    part_no = 1
                encoded_body = msg_data["payload"]["parts"][part_no]["body"]["data"]

            decoded_body = base64.urlsafe_b64decode(encoded_body.encode("UTF-8"))
            current_email.html_body = BeautifulSoup(decoded_body, "html.parser")
            current_email.body = current_email.html_body.text
            current_email.body = current_email.body.replace("&nbsp", "\n")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            success = process_email(current_email, transactions_to_export)
            # Mark email as READ
            try:
                if success and operation_mode == OperationMode.GUI:
                    service.users().messages().modify(
                        userId="me",
                        id=msg["id"],
                        body={"removeLabelIds": ["UNREAD"]},
                    ).execute()
            except Exception as e:
                print(
                    f"Error marking email as READ. Skiping email: {current_email}. Error: {e}"
                )
    print(f"Finished parsing {messages_len} emails\n")


def main():
    operation_mode = OperationMode.DEV
    for arg in sys.argv:
        if arg == "-g":
            operation_mode = OperationMode.GUI
        if arg == "-m":
            operation_mode = OperationMode.MANUAL

    transactions_to_export: list[Transaction] = []
    creds = get_credentials()
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)

    try:
        messages = get_messages(service, operation_mode)
        process_messages(service, transactions_to_export, messages, operation_mode)
        export_to_xlsx(transactions_to_export)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


def countdown(n: int):
    for i in range(n, 0, -1):
        print("Closing in", i, end="\r")
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(traceback.format_exc())
        # print("Fatal error detected!\n\n", e)
    countdown(5)
