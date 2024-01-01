import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email_parser import *
import base64
from bs4 import BeautifulSoup
import re
import csv

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def set_options() -> tuple[int,str]:
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

def export_emails_to_csv(email_list : list[Email]) -> None:
  print("Exporting", len(email_list), "transaction emails")
  headers = ["Date", "Description", "Category", "Price"]
  if email_list == []:
    print("No data to export")
    return
  with open('Emails_output.csv', 'w', newline='', encoding='utf-8') as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(headers)
    for email in email_list:
      temp_row = [email.date, email.transaction_description, email.category, email.transaction_price_str]
      csv_writer.writerow(temp_row)
  
  print("Finished exporting!\n")
  return

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
        "\nExample: 'label:Bancos from:amy@example.com  after:2020/04/16'" \
        "\n - Bank emails: notificacion@notificacionesbaccr.com , AlertasScotiabank@scotiabank.com , bcrtarjestcta@bancobcr.com" \
        "\n\nCheck https://support.google.com/mail/answer/7190?hl=en on how to make a search query." \
      )
  query = input("\n\nSearch query:\n>>> ")
    
  return (max_results, query)

def main():
  emails_to_export : list[Email] = []
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      os.remove("token.json")
      creds.refresh(Request())
    else:
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
    max_emails, search_query = set_options()
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
        current_email.html_body = BeautifulSoup(decoded_body, "lxml")
        current_email.body = current_email.html_body.text
        current_email.body = current_email.body.replace("&nbsp","\n")
      except: 
        pass
      finally:
        append = True
        if ("scotiabank" in current_email.sender.lower()) and ("alerta transacción tarjeta" in current_email.subject.lower()):
          parse_email(current_email, "scotiabank")
        elif ("notificacionesbaccr" in current_email.sender.lower()) and ("notificación de transacción" in current_email.subject.lower()):
          parse_email(current_email, "bac")
        else:
          append = False

        if append:
          emails_to_export.append(current_email)

    print(f"Finished parsing {messages_len} emails\n")
    export_emails_to_csv(emails_to_export)

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  read_classification()
  main()
