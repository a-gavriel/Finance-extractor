from banks.base_bank_processor import BaseBankProcessor
from models.transaction import Transaction, TransactionType
from models.email import Email


class BcrProcessor(BaseBankProcessor):
    @property
    def name(self) -> str:
        return "BCR"

    def identify(self, email: Email):
        return "bcrtarjestcta" in email.sender.lower()

    def process(self, email):
        if self._identify_transaction_type(email) == TransactionType.CARD_MOVEMENT:
            return self._process_card_purchase(email)
        return None

    def _identify_transaction_type(self, email: Email) -> TransactionType:
        if "notificación de transacciones" in email.subject.lower():
            return TransactionType.CARD_MOVEMENT

    def _process_card_purchase(self, email: Email) -> Transaction:
        description = ""
        date = ""
        price = ""
        card = "?"

        html_position = email.html_body.find("th", string="Fecha")
        # Go to column 1
        html_position = html_position.findNext("td")
        date = html_position.text
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
        _approved = html_position.text

        price_crc, price_usd = 0.0, 0.0

        if currency == "COLON COSTA RICA":
            price_crc = BaseBankProcessor.to_price(amount)
            price = "CRC " + amount
        elif currency == "US DOLLAR":
            price_usd = BaseBankProcessor.to_price(amount)
            price = "USD " + amount

        ts = Transaction(
            type=TransactionType.CARD_MOVEMENT,
            amount_raw=price,
            amount_crc=price_crc,
            amount_usd=price_usd,
            description=description,
            date_str=date,
            bank_name=self.name,
            card_num=card,
        )
        ts.set_category()
        return ts
