import re
from datetime import datetime
from enum import Enum

classification_list = {}

def read_classification():
  global classification_list
  with open("classification.txt","r") as f:
    lines = f.readlines()

  current_class = ""
  for line in lines:
    line = line.strip().lower().replace("\n","")
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

      classification_list[current_class] = [[],[]]

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

class Bank(Enum):
  UNASSIGNED = 0
  SCOTIABANK = 1
  BAC = 2
  BCR = 3
  BNCR = 4

class Email:
  def __init__(self):
    self.sender : str = ""
    self.subject : str = ""
    self.date_str : str = ""
    self.html_body : str = ""
    self.body : str = ""
    self.transaction_price_str : str = ""
    self.transaction_description : str = ""
    self.transaction_date_str : str = ""
    self.category : str = ""
    self.price_usd : float = 0.0
    self.price_crc : float = 0.0
    self.card : int = 0
    self.bank : Bank = Bank.UNASSIGNED
    

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
    text : str = ""
    text += "Sender:\t" + self.sender + "\n"
    text += "Subject:\t" + self.subject + "\n"
    text += "Date:\t" + self.date + "\n"
    text += "Description:\t" + self.transaction_description + "\n"
    text += "Price:\t" + self.transaction_price_str + "\n"
    text += "Category:\t" + self.category + "\n"
    return text

  def set_category(self) -> None:
    description = " " + self.transaction_description.lower() + " "
    description = description.replace("."," ").replace("*", " ").replace("-", " ")
    description = description.replace("   "," ").replace("  "," ")
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

def indentify_bank(email: Email) -> Bank:
  if ("scotiabank" in email.sender.lower()) and ("alerta transacción tarjeta" in email.subject.lower()):
    return Bank.SCOTIABANK
  elif ("notificacionesbaccr" in email.sender.lower()) and ("notificación de transacción" in email.subject.lower()):
    return Bank.BAC
  elif ("bcrtarjestcta" in email.sender.lower()) and ("notificación de transacciones" in email.subject.lower()):
    return Bank.BCR
  return Bank.UNASSIGNED

def parse_email(email : Email, bank: Bank = Bank.UNASSIGNED)-> None:
  """
  Reads the email's body and sets its transaction's:
    description  : str
    date  : str
    price : str
    category : str
  """
  if bank == Bank.UNASSIGNED:
    bank = indentify_bank(email)

  if bank == Bank.SCOTIABANK:
    parse_scotiabank(email)
  elif bank == Bank.BAC:
    parse_bac(email)
  elif bank == Bank.BCR:
    parse_bcr(email)
  else:
    raise Exception(f"Error: Bank parser not defined for {bank}")
  
  email.set_category()
  return 



def parse_bcr(email : Email) -> None:
  email.bank = Bank.BCR
  description = ""
  date = ""
  price = ""
  
  html_position = email.html_body.find("th", string="Fecha")
  html_position = html_position.findNext("td") # Go to column 1
  date = html_position.text
  html_position = html_position.findNext("td").findNext("td").findNext("td") # Go to column 4
  amount = html_position.text
  html_position = html_position.findNext("td") # Go to column 5
  currency = html_position.text
  html_position = html_position.findNext("td") # Go to column 6
  description = html_position.text
  html_position = html_position.findNext("td") # Go to column 7
  approved = html_position.text

  if currency == "COLON COSTA RICA":
    email.price_crc = to_price(amount)
    price = "CRC " + amount
  elif currency == 'US DOLLAR':
    email.price_usd = to_price(amount)
    price = "USD " + amount

  email.transaction_price_str = price
  email.transaction_description = description 
  email.transaction_date_str = date
  
  return


def parse_bac(email : Email) -> None:
  email.bank = Bank.BAC
  text : str = email.body
  text = text.replace("\r","")
  while "\n\n" in text:
    text = text.replace("\n\n\n\n","\n")
    text = text.replace("\n\n\n","\n")
    text = text.replace("\n\n","\n")

  DESCRIPTION_PATTERN = "Comercio:\n(.*)\n"
  DATE_PATTERN = "Fecha:\n(.*)\n"
  PRICE_PATTERN = "Monto:\n(.*)\n"
  CARD_PATTERN = r"\*(\d+)\nAutorizaci"
  description = ""
  date = ""
  price = ""
  card = ""
  
  description_match = re.findall(DESCRIPTION_PATTERN, text)
  if description_match:
    description = description_match[0].strip()

  date_match = re.findall(DATE_PATTERN, text)
  if date_match:
    date = date_match[0].strip()

  price_match = re.findall(PRICE_PATTERN, text)
  if price_match:
    price = price_match[0].strip()

  card_match =  re.findall(CARD_PATTERN, text)
  if card_match:
    card = card_match[0].strip()
    email.card = int(card)

  if "USD" in price:
    val = price.replace("USD", "")
    email.price_usd = to_price(val)
  elif "CRC" in price:
    val = price.replace("CRC", "")
    email.price_crc = to_price(val)

  email.transaction_description = description 
  email.transaction_date_str = date
  email.transaction_price_str = price
  
  return

def parse_scotiabank(email : Email) -> None:
  email.bank = Bank.SCOTIABANK
  text : str = email.body
  text = text.replace("&nbsp", " ")

  DESCRIPTION_PATTERN = r"Scotiabank le notifica que la transacción realizada en (.*), el día"
  DATE_PATTERN = r"el día (.*) a las"
  PRICE_PATTERN = r"referencia \d* por (.*), fue "
  CARD_PATTERN = r"terminada en (\d*) "
  description = ""
  date = ""
  price = ""
  card = ""
  
  description_match = re.findall(DESCRIPTION_PATTERN, text)
  if description_match:
    description = description_match[0]
  
  date_match = re.findall(DATE_PATTERN, text)
  if date_match:
    date = date_match[0]
  
  card_match = re.findall(CARD_PATTERN, text)
  if card_match:
    card = card_match[0]
    email.card = int(card)

  price_match = re.findall(PRICE_PATTERN, text)
  if price_match:
    price = price_match[0]

  if "USD" in price:
    val = price.replace("USD", "")
    email.price_usd = to_price(val)
  elif "CRC" in price:
    val = price.replace("CRC", "")
    email.price_crc = to_price(val)

  email.transaction_description, email.transaction_date_str, \
          email.transaction_price_str = description, date, price
  
  return 


def to_price(number : str) -> float:
  number = number.strip()
  if not number:
    return 0.0
  
  has_period = "." in number
  has_comma = "," in number
  if has_period:
    pos_p = number.index(".")
  if has_comma:
    pos_c = number.index(",")
  if has_comma and has_period:
    if pos_p < pos_c:
      number = number.replace(".","")
    else:
      number = number.replace(",","")
  
  number = number.replace(",",".")
  val = float(number)
  return val