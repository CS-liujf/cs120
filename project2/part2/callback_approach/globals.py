import threading
from enum import Enum

import numpy as np
from scipy import integrate

F = 48000

BLOCK_SIZE = 2048
CHANNELS = 1
DEFAULT_DEVICE = 3
LATENCY = 'low'


class NodeType(str, Enum):
    TRANSMITTER = 'transmitter'
    RECEIVER = 'receiver'


class NodeStatus(str, Enum):
    IDLE = 'idle'
    SENDING_DATA = 'sending_data'
    SENDING_ACK = 'sending_ACK'


def generate_preamble():
    t = np.linspace(0, 1, F, endpoint=True, dtype=np.float32)[0:80]
    f_p = np.concatenate(
        [np.linspace(2000, 10000, 40),
         np.linspace(10000, 2000, 40)])
    return (np.sin(2 * np.pi * integrate.cumulative_trapezoid(f_p, t))).astype(
        np.float32)


TOTAL_BITS = 50000
BITS_PER_FRAME = 200
TOTAL_FRAME_NUMBER = TOTAL_BITS // BITS_PER_FRAME

PREAMBLE = generate_preamble()
PREAMBLE_THRESHOLD = 210
PREAMBLE_TRY_LENGTH = 150
# each time try to detect preamble with following length
DETECT_PREAMBLE_LENGTH = int(1.5 * len(PREAMBLE))
SIGNAL_ONE = [-0.9, -0.9, -0.9, 0.9, 0.9, 0.9]
SIGNAL_ZERO = [0.9, 0.9, 0.9, -0.9, -0.9, -0.9]
BIT_SIGNAL_LENGTH = len(SIGNAL_ZERO)
# length of bits contained(remove preamble), the 1 is for frame_index, 8 is for crc
FRAME_DATA_LENGTH = BIT_SIGNAL_LENGTH*(BITS_PER_FRAME+1+8)
# ack length
ACK_LENGTH = 8 * BIT_SIGNAL_LENGTH
# each time check how many acks
CHECK_ACK_RECEIVED_RANGE_SIZE = 10

input_file_name = '../../INPUT.txt'
Tx_frame = []
Rx_frame = []
# the index of an output frame
output_index = 0
# the buffer used to store all in coming data
all_buffer = []
ack_buffer = []
# the sending time of each data frame
data_send_time = [0.0] * TOTAL_FRAME_NUMBER
# the received data
received_data = [None] * TOTAL_FRAME_NUMBER
# receive status of each frame
frame_received_status = [False] * TOTAL_FRAME_NUMBER
# receive ack status
ack_received_status = [False] * TOTAL_FRAME_NUMBER
retransmit_time = 0.5
retransmit_count = [0] * TOTAL_FRAME_NUMBER
max_retransmit = 7
sending_ack_index = 0
received_frames = 0
node_status = 'idle'

# thread synchronization
MAC_condition = threading.Condition()
Tx_condition = threading.Condition()
Rx_condition = threading.Condition()
