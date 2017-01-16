#!/usr/bin/env python

import sys
import rethinkdb as r
from qdserver.model import Orders, run

print("DELETE ORDER TABLE? (yes/no)")
result = sys.stdin.readline()
if result.strip() == 'yes':
    print("deleting order table")
    run(Orders.delete())
else:
    print("not deleting anything!")
