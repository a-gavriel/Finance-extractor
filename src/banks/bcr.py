import re
from datetime import datetime

from banks.base_bank_processor import BaseBankProcessor
from models.transaction import Transaction, TransactionType
from models.email import Email


class BcrProcessor(BaseBankProcessor):
    @property
    def name(self) -> str:
        return "BCR"

    def identify(self, email: Email):
        sender = email.sender.lower()
        return ("bcrtarjestcta" in sender) or ("mensajero@bancobcr.com" in sender)

    def process(self, email):
        if self._identify_transaction_type(email) == TransactionType.CARD_MOVEMENT:
            return self._process_card_purchase(email)
        elif self._identify_transaction_type(email) == TransactionType.SINPE_MOVIL:
            return self._process_sinpe(email)
        return None

    def _identify_transaction_type(self, email: Email) -> TransactionType:
        sender = email.sender.lower()
        subject = email.subject.lower()
        if ("notificación de transacciones" in subject) and ("bcrtarjestcta" in sender):
            return TransactionType.CARD_MOVEMENT
        elif ("mensajero@bancobcr.com" in sender) and ("sinpemovil" in subject):
            return TransactionType.SINPE_MOVIL

    @staticmethod
    def _get_datetime(text: str, email_dt_str) -> "datetime":
        DATETIME_PATTERN = r"(\d{2}/\d{2}/\d{4}) (\d{1,2}:\d{2})"
        dt = BaseBankProcessor.get_default_date_time(email_dt_str)

        try:
            date_time_match = re.search(DATETIME_PATTERN, text)
            if date_time_match:
                date_str, time_str = date_time_match.groups()
                full_str = f"{date_str} {time_str}"
                dt = datetime.strptime(full_str, "%d/%m/%Y %H:%M")
                return dt
        except Exception as e:
            print("Error parsing datetime of BCR email. Args: \n"
                  f"text: {text}, email_dt_str: {email_dt_str}")
            print(e)
        return dt

    def _process_sinpe(self, email: Email) -> Transaction:
        dt = BaseBankProcessor.get_default_date_time(email.date_str)

        # Buscar número de referencia
        dest_match = re.search(r"Tel.fono Destino:\s*(\d+)", email.body)
        dest_num = dest_match.group(1) if dest_match else None

        amount_match = re.search(r"Monto:\s*([\d.,]+)", email.body)
        amount_raw = amount_match.group(1) if amount_match else None
        amount_crc: float = BaseBankProcessor.to_price(amount_raw)

        datetime_match = re.search(
            r"el (\d{2}/\d{2}/\d{4}) a las (\d{1,2}:\d{2}\s*[AP]M)", email.body
        )
        if datetime_match:
            date_str, time_str = datetime_match.groups()
            dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %I:%M %p")

        desc_match = re.search(r"Motivo:(.*)", email.body)
        description = desc_match.group(1) if desc_match else None
        description = description.strip() + f" | SINPE → {dest_num}"
        ts = Transaction(
            type=TransactionType.CARD_MOVEMENT,
            amount_raw=amount_raw,
            amount_crc=amount_crc,
            amount_usd=0,
            description=description,
            date_time=dt,
            bank_name=self.name,
            card_num="?",
        )
        ts.set_category()
        return ts

    def _process_card_purchase(self, email: Email) -> Transaction:
        description = ""
        date = ""
        price = ""
        card = "?"

        html_position = email.html_body.find("th", string="Fecha")
        # Go to column 1
        html_position = html_position.findNext("td")
        date = html_position.text
        dt = BcrProcessor._get_datetime(date, email.date_str)

        # Go to column 4
        html_position = html_position.findNext("td").findNext("td").findNext("td")
        amount = html_position.text
        # Go to column 5
        html_position = html_position.findNext("td")
        currency = html_position.text
        # Go to column 6
        html_position = html_position.findNext("td")
        description = html_position.text
        # Go to column 7
        html_position = html_position.findNext("td")
        approved = (html_position.text != "Negada")
        price_crc, price_usd = 0.0, 0.0


        if currency == "COLON COSTA RICA":
            price_crc = BaseBankProcessor.to_price(amount)
            price = "CRC " + amount
        elif currency == "US DOLLAR":
            price_usd = BaseBankProcessor.to_price(amount)
            price = "USD " + amount

        if not approved:
            price_crc, price_usd = 0.0, 0.0

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
