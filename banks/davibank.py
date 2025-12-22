import re
from datetime import datetime

from banks.base_bank_processor import BaseBankProcessor
from models.transaction import Transaction, TransactionType
from models.email import Email


class DavibankProcessor(BaseBankProcessor):
    @property
    def name(self) -> str:
        return "Davibank"

    def identify(self, email: Email):
        return "davibank" in email.sender.lower()

    def process(self, email):
        if self._identify_transaction_type(email) == TransactionType.CARD_MOVEMENT:
            return self._process_card_purchase(email)
        return None

    def _identify_transaction_type(self, email: Email) -> TransactionType:
        if "alerta transacción tarjeta" in email.subject.lower():
            return TransactionType.CARD_MOVEMENT

    @staticmethod
    def _get_datetime(text: str, email_dt_str) -> "datetime":
        DATE_PATTERN = r"el día (.*) a las"
        DATETIME_PATTERN = r"el día (\d{2}/\d{2}/\d{4}) a las (\d{1,2}:\d{2} [AP]M)"
        dt = BaseBankProcessor.get_default_date_time(email_dt_str)

        try:
            date_time_match = re.search(DATETIME_PATTERN, text)
            if date_time_match:
                date_str, time_str = date_time_match.groups()
                full_str = f"{date_str} {time_str}"
                dt = datetime.strptime(full_str, "%d/%m/%Y %I:%M %p")
                return dt

            date_match = re.findall(DATE_PATTERN, text)
            if date_match:
                dt = datetime.strptime(date_match[0], "%d/%m/%Y")
                return dt
        except Exception as e:
            print(e)

        return dt

    def _process_card_purchase(self, email: Email) -> Transaction:
        """Process a transaction using a card."""

        text: str = email.body
        text = text.replace("&nbsp", " ")

        DESCRIPTION_PATTERN = (
            r"le notifica que la transacción realizada en (.*), el día"
        )
        PRICE_PATTERN = r"referencia \d* por (.*), fue "
        CARD_PATTERN = r"terminada en (\d*) "
        description = ""
        amount_raw = ""
        card = ""
        dt: "datetime" = DavibankProcessor._get_datetime(text, email.date_str)

        description_match = re.findall(DESCRIPTION_PATTERN, text)
        if description_match:
            description = description_match[0]


        card_match = re.findall(CARD_PATTERN, text)
        if card_match:
            card = card_match[0].strip()

        price_match = re.findall(PRICE_PATTERN, text)
        if price_match:
            amount_raw = price_match[0]

        amount_crc = 0.0
        amount_usd = 0.0

        if "USD" in amount_raw:
            val = amount_raw.replace("USD", "")
            amount_usd = BaseBankProcessor.to_price(val)
        elif "CRC" in amount_raw:
            val = amount_raw.replace("CRC", "")
            amount_crc = BaseBankProcessor.to_price(val)

        ts = Transaction(
            type=TransactionType.CARD_MOVEMENT,
            amount_raw=amount_raw,
            amount_crc=amount_crc,
            amount_usd=amount_usd,
            description=description,
            date_time=dt,
            bank_name=self.name,
            card_num=card,
        )
        ts.set_category()
        return ts
