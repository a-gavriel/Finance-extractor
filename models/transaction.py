from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class TransactionType(Enum):
    CARD_MOVEMENT = "card_movement"
    SINPE_MOVIL = "sinpe_movil"
    ATM_WITHDRAWAL = "atm_withdrawal"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"


classification_list = {}


def read_classification():
    global classification_list
    with open("classification.txt", "r") as f:
        lines = f.readlines()

    current_class = ""
    for line in lines:
        line = line.strip().lower().replace("\n", "")
        if len(line) == 0:
            pass
        elif line[0] == "#":
            pass
        elif line.startswith("class:"):
            current_class = f"temp{len(classification_list)+1}"
            if len(line) > 6:
                line = line[6:].strip()
                if (len(line) != 0) and (line not in classification_list):
                    current_class = line.title()

            classification_list[current_class] = [[], []]

        elif line.startswith("include:"):
            include_list = []
            if len(line) > 8:
                line = line[8:].strip()
                if len(line) != 0:
                    include_list = line.split(",")
                    include_list = [i.strip() for i in include_list]

            classification_list[current_class][0].extend(include_list)

        elif line.startswith("exclude:"):
            exclude_list = []
            if len(line) > 8:
                line = line[8:].strip()
                if len(line) != 0:
                    exclude_list = line.split(",")
                    exclude_list = [i.strip() for i in exclude_list]

            classification_list[current_class][1].extend(exclude_list)
        else:
            pass

    return


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
        description = " " + self.description.lower() + " "
        description = description.replace(".", " ").replace("*", " ").replace("-", " ")
        description = description.replace("   ", " ").replace("  ", " ")
        for category, (include_words, exclude_words) in classification_list.items():
            excluded = False
            for word in exclude_words:
                word = " " + word + " "
                if excluded:
                    break
                if word in description:
                    excluded = True
                    break
            if not excluded:
                for word in include_words:
                    word = " " + word + " "
                    if word in description:
                        self.category = category
                        return
        self.category = ""
        return


if not classification_list:
    read_classification()
