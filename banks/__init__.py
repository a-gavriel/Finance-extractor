from .scotiabank import ScotiabankProcessor
from .bac import BacProcessor
from .bcr import BcrProcessor

# Lista de procesadores activos
BANK_PROCESSORS = [
    ScotiabankProcessor(),
    BacProcessor(),
    BcrProcessor(),
]
