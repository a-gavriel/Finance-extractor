# banks/base_bank_processor.py
from abc import ABC, abstractmethod
from datetime import datetime
from models.email import Email
from models.transaction import Transaction


class BaseBankProcessor(ABC):
    """Base abstract class for all bank processors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Readable name of the bank (e.g., 'Scotiabank')"""

    @abstractmethod
    def identify(self, email: Email) -> bool:
        """Returns True if the email belongs to this bank."""

    @abstractmethod
    def process(self, email: Email) -> Transaction | None:
        """Parses the email and returns a Transaction if applicable."""

    @staticmethod
    def to_price(raw_price : str) -> float:
        """
        Converts from a raw price number which may use a decimal separator
        of comma or dot into a float
        """
        number = raw_price.strip()
        if not number:
            return 0.0

        pos_p = number.find(".")
        pos_c = number.find(",")
        # If it has both symbols, identify which is the decimal separator
        # and remove the other one
        if (pos_p != -1) and (pos_c != -1):
            if pos_p < pos_c:
                number = number.replace(".","")
            else:
                number = number.replace(",","")

        # Convert decimal separator to point
        number = number.replace(",",".")
        val = float(number)
        return val

    @staticmethod
    def get_default_date_time(email_date_time: str):
        date_time = datetime.strptime(email_date_time, "%a, %d %b %Y %H:%M:%S %z")
        return date_time
