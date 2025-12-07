import re
from datetime import datetime

from banks.base_bank_processor import BaseBankProcessor
from models.transaction import Transaction, TransactionType
from models.email import Email


class BacProcessor(BaseBankProcessor):
    @property
    def name(self) -> str:
        return "BAC"

    def identify(self, email: Email):
        return "notificacionesbaccr" in email.sender.lower()

    def process(self, email):
        if self._identify_transaction_type(email) == TransactionType.CARD_MOVEMENT:
            return self._process_card_purchase(email)
        return None

    def _identify_transaction_type(self, email: Email) -> TransactionType:
        if "notificación de transacción" in email.subject.lower():
            return TransactionType.CARD_MOVEMENT

    @staticmethod
    def _get_datetime(text: str, email_dt_str) -> "datetime":
        DATE_PATTERN = r"Fecha:\s*\n?\s*([A-Za-z]{3} \d{1,2}, \d{4})"
        DATETIME_PATTERN =  r"Fecha:\s*\n?\s*([A-Za-z]{3} \d{1,2}, \d{4}, \d{1,2}:\d{2})"
        dt = BaseBankProcessor.get_default_date_time(email_dt_str)

        month_map = {
            "Ene": "Jan",
            "Feb": "Feb",
            "Mar": "Mar",
            "Abr": "Apr",
            "May": "May",
            "Jun": "Jun",
            "Jul": "Jul",
            "Ago": "Aug",
            "Sep": "Sep",
            "Oct": "Oct",
            "Nov": "Nov",
            "Dic": "Dec",
        }


        try:
            datetime_match = re.search(DATETIME_PATTERN, text)
            if datetime_match:
                date_str = datetime_match.group(1)
                date_str = date_str.replace(",", "")

                # Convert month to spanish
                parts = date_str.split()
                parts[0] = month_map[parts[0]]
                date_str_eng = " ".join(parts)
                dt = datetime.strptime(date_str_eng, "%b %d %Y %H:%M")
                return dt

            date_match = re.search(DATE_PATTERN, text)
            if date_match:
                date_str = date_match.group(1)
                date_str = date_str.replace(",", "")

                # Convert month to spanish
                parts = date_str.split()
                parts[0] = month_map[parts[0]]
                date_str_eng = " ".join(parts)
                dt = datetime.strptime(date_str, "%b %d %Y")
                return dt
        except Exception as e:
            print(e)

        return dt


    def _process_card_purchase(self, email: Email) -> Transaction:
        DESCRIPTION_PATTERN = r"Comercio:\n(.*)\n"
        PRICE_PATTERN = r"Monto:\n(.*)\n"
        CARD_PATTERN = r"\*(\d+)\nAutorizaci"

        text: str = email.body
        text = text.replace("\r", "")
        while "\n\n" in text:
            text = text.replace("\n\n\n\n", "\n")
            text = text.replace("\n\n\n", "\n")
            text = text.replace("\n\n", "\n")

        description = ""
        price = ""
        card = ""
        dt = BacProcessor._get_datetime(text, email.date_str)

        description_match = re.findall(DESCRIPTION_PATTERN, text)
        if description_match:
            description = description_match[0].strip()

        price_match = re.findall(PRICE_PATTERN, text)
        if price_match:
            price = price_match[0].strip()

        card_match = re.findall(CARD_PATTERN, text)
        if card_match:
            card = card_match[0].strip()

        price_usd, price_crc = 0.0, 0.0

        if "USD" in price:
            val = price.replace("USD", "")
            price_usd = BaseBankProcessor.to_price(val)
        elif "CRC" in price:
            val = price.replace("CRC", "")
            price_crc = BaseBankProcessor.to_price(val)

        ts = Transaction(
            type=TransactionType.CARD_MOVEMENT,
            amount_raw=price,
            amount_crc=price_crc,
            amount_usd=price_usd,
            description=description,
            date_time=dt,
            bank_name=self.name,
            card_num=card,
        )
        ts.set_category()
        return ts
