from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from lib.categorizer import categorize_transaction

class TransactionType(Enum):
    CARD_MOVEMENT = "card_movement"
    SINPE_MOVIL = "sinpe_movil"
    ATM_WITHDRAWAL = "atm_withdrawal"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"



@dataclass
class Transaction:
    type: TransactionType
    amount_crc: float
    amount_usd: float
    description: str
    date_time: "datetime"
    card_num: str
    bank_name: str
    amount_raw: str = ""
    category: str = ""

    @property
    def datetime(self):
        return self.date_time.strftime("%Y-%m-%d_T%H-%M-%S")

    @property
    def date(self):
        return self.date_time.strftime("%Y-%m-%d")

    def __repr__(self) -> str:
        text: str = ""
        text += "Date:\t" + self.date + "\n"
        text += "Description:\t" + self.description + "\n"
        text += "Price:\t" + self.amount_raw + "\n"
        text += "Category:\t" + self.category + "\n"
        return text


    def set_category(self) -> None:
        self.category = categorize_transaction(self.description)
        return
