import threading
from enum import Enum

import numpy as np
from scipy import integrate

F = 48000

BLOCK_SIZE = 2048
CHANNELS = 1
DEFAULT_DEVICE = 3
LATENCY = 0.001


class NodeStatus(str, Enum):
    IDLE = 'idle'
    SENDING_DATA = 'sending_data'
    SENDING_ACK = 'sending_ACK'


PREAMBLE_THRESHOLD = 20
PREAMBLE_TRY_LENGTH = 150
# each time check how many acks
CHECK_ACK_RECEIVED_RANGE_SIZE = 100

input_file_name = 'project2/INPUT.txt'
Tx_frame = np.zeros(1)
receive_frame_index = 0
# the index of sounddevice output
sd_output_index = 0
# the incoming data processing index
curr_pointer = 0
# the buffer used to store all in coming data
all_buffer = []
ack_buffer = []
# the sending time of each data frame
data_send_time = [0.0]
# receive ack status
ack_received_status = [False]
RETRANSMIT_TIME = 0.3
retransmit_count = [0]
MAX_RETRANSMIT = 20
node_status = NodeStatus.IDLE

# thread synchronization
MAC_condition = threading.Condition()
Tx_condition = threading.Condition()
Rx_condition = threading.Condition()

# carrier wave
SIGNAL_ONE = [-0.5, -0.5, -0.5, 0.5, 0.5, 0.5]
SIGNAL_ZERO = [0.5, 0.5, 0.5, -0.5, -0.5, -0.5]
BIT_LEN = len(SIGNAL_ZERO)

# incoming data list
incoming_MACs = []
# incoming data handle index
incoming_MACs_handle_index = 0
# incoming ack list
incoming_acks = []
# incoming ack handle index
incoming_acks_handle_index = 0
# output data list, contains of strings with 01
output_data_list = []
output_data_index = 0

# the bit number of each MAC field
DEST_FIELD_LEN = 4  # destination of the frame
SRC_FIELD_LEN = 4  # source of the frame
TYPE_FIELD_LEN = 4  # type of this frame, ack or data
SEQ_FIELD_LEN = 4  # sequence of this frame, used to differentiate the frames
MAC_HEADER_LEN = DEST_FIELD_LEN + SRC_FIELD_LEN + TYPE_FIELD_LEN + SEQ_FIELD_LEN
MAC_DATA_PAYLOAD_LEN = 200  # MAC data payload length
MAC_ACK_PAYLOAD_LEN = 0  # MAC ack length

# the bit number of each PHY field
PREAMBLE_LEN = 80  # length of preamble
LEN_LEN = 8  # length of MAC frame, 0~255, the length of MAC frame
PHY_DATA_PAYLOAD_LEN = MAC_HEADER_LEN + MAC_DATA_PAYLOAD_LEN  # length of phy payload
PHY_ACK_PAYLOAD_LEN = MAC_HEADER_LEN + MAC_ACK_PAYLOAD_LEN  # length of phy payload
CRC_LEN = 8  # length of crc checksum, crc is only applied to PHY Payload part, doesn't contain Len field
PHY_FRAME_LEN = PREAMBLE_LEN + PHY_DATA_PAYLOAD_LEN + LEN_LEN + CRC_LEN  # max length of PHY frame


def generate_preamble():
    t = np.linspace(0, 1, F, endpoint=True, dtype=np.float32)[0:PREAMBLE_LEN]
    f_p = np.concatenate(
        [np.linspace(2000, 10000, PREAMBLE_LEN // 2),
         np.linspace(10000, 2000, PREAMBLE_LEN // 2)])
    return (np.sin(2 * np.pi * integrate.cumulative_trapezoid(f_p, t))).astype(np.float32)


PREAMBLE = generate_preamble()
