from datetime import datetime


class Email:
    def __init__(self):
        self.sender: str = ""
        self.subject: str = ""
        self.date_str: str = ""
        self.html_body: str = ""
        self.body: str = ""

    @property
    def datetime(self):
        date_time = datetime.strptime(self.date_str, "%a, %d %b %Y %H:%M:%S %z")
        # TODO: offset timezone to -6
        return date_time.strftime("%Y-%m-%d_T%H-%M-%S")

    @property
    def date(self):
        date = datetime.strptime(self.date_str, "%a, %d %b %Y %H:%M:%S %z")
        # TODO: offset timezone to -6
        return date.strftime("%Y-%m-%d")

    def __repr__(self) -> str:
        text: str = ""
        text += "Sender:\t" + self.sender + "\n"
        text += "Subject:\t" + self.subject + "\n"
        text += "Date:\t" + self.date + "\n"
        return text
