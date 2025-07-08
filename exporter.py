
import csv
from email_parser import Email
import xlwt
from datetime import datetime

def export_emails_to_csv(email_list : list[Email]) -> None:
  print("Exporting", len(email_list), "transaction emails")
  headers = ["Date", "Description", "Category", "Price", "Price USD", "Price CRC", "Bank", "Card"]
  if email_list == []:
    print("No data to export")
    return
  with open('Emails_output.csv', 'w', newline='', encoding='utf-8') as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(headers)
    for email in email_list:
      temp_row = [email.date, \
                  email.transaction_description, \
                  email.category, \
                  email.transaction_price_str, \
                  email.price_usd, \
                  email.price_crc, \
                  email.bank, \
                  email.card]
      csv_writer.writerow(temp_row)
  
  print("Finished exporting!\n")
  return

def export_emails_to_xlsx(email_list : list[Email]) -> None:
  print("Exporting", len(email_list), "transaction emails")
  

  if email_list == []:
    print("No data to export")
    return
  
  wb = xlwt.Workbook()
  ws = wb.add_sheet('Email Data')
  
  headers = ["Date", "Description", "Category", "Price", "Price USD", "Price CRC", "Bank", "Card"]
  for j,val in enumerate(headers):
    ws.write(0,j, val)

  for i, email in enumerate(email_list):
      temp_row = [email.date, \
                  email.transaction_description, \
                  email.category, \
                  email.transaction_price_str, \
                  email.price_usd, \
                  email.price_crc, \
                  email.bank, \
                  email.card ]
      for j,val in enumerate(temp_row):
        ws.write(i+1,j, val)

  timestamp = datetime.today().strftime('%Y-%m-%d')
  wb.save(f"Finance-{timestamp}.xls")
  print("Finished exporting!\n")
  return


