"""
Exporter module of transactions to xlsx or csv formats
"""

import csv
from datetime import datetime

import xlwt

from models.transaction import Transaction


def export_to_csv(transaction_list: list[Transaction]) -> None:
    print("Exporting", len(transaction_list), "transaction emails")
    headers = [
        "Date",
        "Description",
        "Category",
        "Price",
        "Price USD",
        "Price CRC",
        "Bank",
        "Card",
    ]
    if transaction_list == []:
        print("No data to export")
        return
    with open("Emails_output.csv", "w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(headers)
        for ts in transaction_list:
            temp_row = [
                ts.date,
                ts.description,
                ts.category,
                ts.amount_raw,
                ts.amount_usd,
                ts.amount_crc,
                ts.bank_name,
                ts.card_num,
            ]
            csv_writer.writerow(temp_row)

    print("Finished exporting!\n")
    return


def export_to_xlsx(transaction_list: list[Transaction]) -> None:
    print("Exporting", len(transaction_list), "transaction emails")

    if transaction_list == []:
        print("No data to export")
        return

    wb = xlwt.Workbook()
    ws = wb.add_sheet("Email Data")

    headers = [
        "Date",
        "Description",
        "Category",
        "Price",
        "Price USD",
        "Price CRC",
        "Bank",
        "Card",
    ]
    for j, val in enumerate(headers):
        ws.write(0, j, val)

    for i, ts in enumerate(transaction_list):
        temp_row = [
            ts.date,
            ts.description,
            ts.category,
            ts.amount_raw,
            ts.amount_usd,
            ts.amount_crc,
            ts.bank_name,
            ts.card_num,
        ]
        for j, val in enumerate(temp_row):
            ws.write(i + 1, j, val)

    timestamp = datetime.today().strftime("%Y-%m-%d")
    wb.save(f"Finance-{timestamp}.xls")
    print("Finished exporting!\n")
    return
