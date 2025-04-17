import sys
import gc
gc.enable()

buffer = bytearray()

while True:
    new_line = sys.stdin.readline()
    sys.stdout.write(new_line)