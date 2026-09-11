from .davibank import DavibankProcessor
from .bac import BacProcessor
from .bcr import BcrProcessor
from .scotiabank import ScotiabankProcessor

# Lista de procesadores activos
BANK_PROCESSORS = [
    DavibankProcessor(),
    BacProcessor(),
    BcrProcessor(),
    ScotiabankProcessor(),
]
