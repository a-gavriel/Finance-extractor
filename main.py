import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email_parser import *
from exporter import *
from select_calendar import select_date
import base64
from bs4 import BeautifulSoup
import time
import traceback
import sys

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.labels"]


def set_options(use_default_options: bool) -> tuple[int,str]:
  # Default options are:
  #       results: 300
  #       query: "label:Bancos after:YYYY/MM/DD"
  if use_default_options:
    selected_date = []
    select_date(selected_date)
    if selected_date:
      result = 300, f"label:Bancos after:{selected_date[0]}  before:{selected_date[1]}"
      print(f"Search Query:\n - limit={result[0]}\n - query={result[1]}")
      return result

  # Here we define the default value for the options
  result = (0, "")

  # In case we hardwired the options, return
  if (result[0] != 0) and (result[1] != ""):
    return result

  while True:
    result = define_options()
    print("\n----------------------")
    print(f"Selected options:\n  max results:\t{result[0]}\n  query:\t{result[1]}")
    print("\n----------------------\n")
    resume = input("Continue (y/n):").lower().strip()
    if resume[0] == "y":
      print("")
      break
  
  return result

def define_options() -> tuple[int,str]:
  max_results : int = 100
  while True:
    try:
      max_results = int(input("Max results [max=500]:").strip())
      if max_results < 1 or max_results > 500:
        raise Exception("Must be between 1 and 500")
      else:
        break
    except Exception:
      print("Invalid input. Please try again!")

  print("\nPlease input the search query to use." \
        "\nTake into consideration that the search by date uses the timezone of UTC" \
        "\nExample: 'label:Bancos from:AlertasScotiabank@scotiabank.com  after:2024/04/16'" \
        "\n - Bank emails: notificacion@notificacionesbaccr.com , AlertasScotiabank@scotiabank.com , bcrtarjestcta@bancobcr.com" \
        "\n\nCheck https://support.google.com/mail/answer/7190?hl=en on how to make a search query." \
      )
  query = input("\n\nSearch query:\n>>> ")
    
  return (max_results, query)

def main():
  use_default_options = 0
  if len(sys.argv) == 2:
    if sys.argv[1] == "-q":
      use_default_options = 1

  emails_to_export : list[Email] = []
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if os.path.exists("token.json"):
      os.remove("token.json")
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    
    # request a list of all the messages 
    max_emails, search_query = set_options(use_default_options)
    result = service.users().messages().list(maxResults=max_emails, userId='me', q=search_query).execute() 
    messages = result.get('messages') 
    messages_len = len(messages)
    print("Found", messages_len, "messages that match the search query\n")
    
    # messages is a list of dictionaries where each dictionary contains a message id. 
    # iterate through all the messages 
    for i,msg in enumerate(messages):
      print(f"Parsing emails: {i+1}/{messages_len}", end="\r", flush=True)
      # Get the message from its id 
      msg_data = service.users().messages().get(userId='me', id=msg['id']).execute() 

      headers = msg_data['payload']['headers'] 
      current_email = Email()
      # Look for Subject and Sender Email in the headers 
      for d in headers: 
        if d['name'] == 'Subject': 
          current_email.subject = d['value'] 
        if d['name'] == 'From': 
          current_email.sender = d['value'] 
        if d['name'] == "X-Received":
          current_email.date_str = d['value']
          current_email.date_str = current_email.date_str[current_email.date_str.rfind(";")+1:].strip()
          current_email.date_str = current_email.date_str[:current_email.date_str.rfind("(")].strip()

      current_email.body = "Not decrypted"

      try: 
        # The Body of the message is in Encrypted format. So, we have to decode it. 
        # Get the data and decode it with base 64 decoder.
        if  msg_data['payload']['body']['size'] > 0:
          encoded_body = msg_data['payload']['body']['data']
        elif len(msg_data['payload']['parts']) > 0:
          part_no = 0
          if msg_data['payload']['parts'][0]['mimeType'] == "text/html":
            part_no = 0
          elif msg_data['payload']['parts'][1]['mimeType'] == "text/html":
            part_no = 1
          encoded_body = msg_data['payload']['parts'][part_no]['body']['data']
          

        decoded_body = base64.urlsafe_b64decode(encoded_body.encode('UTF-8'))
        current_email.html_body = BeautifulSoup(decoded_body, "html.parser")
        current_email.body = current_email.html_body.text
        current_email.body = current_email.body.replace("&nbsp","\n")
      except: 
        pass
      finally:
        try:
          parse_email(current_email)
          service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()
          emails_to_export.append(current_email)
        except Exception as e:
          print(f"Error parsing email. Skiping email: {current_email}. Error: {e}")

    print(f"Finished parsing {messages_len} emails\n")
    export_emails_to_xlsx(emails_to_export)

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


def countdown(n : int):
  for i in range(n,0,-1):
    print("Closing in", i, end="\r")
    time.sleep(1) 

if __name__ == "__main__":
  try:
    read_classification()
    main()
  except Exception as e:
    print(traceback.format_exc())
    #print("Fatal error detected!\n\n", e)
  countdown(5)
