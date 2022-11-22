from globals import *
from collections import Counter


class MacFrame:
    def __init__(self, bits_frame):
        curr = 0
        self.dest = None
        curr += DEST_FIELD_LEN
        self.src = None
        curr += SRC_FIELD_LEN
        self.type = Counter(bits_frame[curr:curr + TYPE_FIELD_LEN]).most_common()[0][0]  # 0 for data, 1 for ack
        curr += TYPE_FIELD_LEN
        self.seq = int(bits_frame[curr:curr + SEQ_FIELD_LEN], 2)
        curr += SEQ_FIELD_LEN
        self.payload = bits_frame[curr:]
