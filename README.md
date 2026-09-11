# Finance Tracker 

This finance tracker uses gmail API to access the bank emails and export their data for further use.

## Setup

[How to setup Gmail API](https://developers.google.com/gmail/api/quickstart/python)

## Run

From Windows File Explorer, double-click one of the root batch files:

- `run_email_processor.bat` processes Gmail bank emails and exports the transactions.
- `run_spreadsheet_processor.bat` asks for an `.xlsx` file and exports the normalized transactions.

Both launchers create/use `.venv`, install `requirements.txt`, and run the selected script from the project root.

## Reference

[Search operators you can use with Gmail](https://support.google.com/mail/answer/7190?hl=en)

[Method: users.messages.list](https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list)


## Ignored file
The classification.txt file is being ignored future changes. Check [This link](https://stackoverflow.com/questions/4348590/how-can-i-make-git-ignore-future-revisions-to-a-file) on how to do it.