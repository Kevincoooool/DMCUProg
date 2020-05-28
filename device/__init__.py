import collections

from . import STM32F103
from . import STM32F103_LS
from . import STM32F405
from . import STM32F405_LS
from . import SWM320


Devices = collections.OrderedDict([
    ('STM32F103C8',    STM32F103.STM32F103C8),
    ('STM32F103C8-LS', STM32F103_LS.STM32F103C8),
    ('STM32F103RC',    STM32F103.STM32F103RC),
    ('STM32F103RC-LS', STM32F103_LS.STM32F103RC),
    ('STM32F405RG',    STM32F405.STM32F405RG),
    ('STM32F405RG-LS', STM32F405_LS.STM32F405RG),
    ('SWM320',         SWM320.SWM320),
])
