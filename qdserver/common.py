import string
import random
from curry.typing import alias

#=========================================================================#
# Server Definitions
#=========================================================================#

ID          = alias('ID', str)
TimeStamp   = alias('TimeStamp', float)
Receipt     = alias('Receipt', str)
UserName    = alias('UserName', str)

#=========================================================================#
# Utils
#=========================================================================#

characters = string.ascii_letters + '0123456789!?@*$+/|'

def shortid():
    return ''.join(random.sample(characters, 3))
