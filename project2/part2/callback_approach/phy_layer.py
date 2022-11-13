import sys
import time
from threading import Thread

from general import *
from globals import *


class MAC(Thread):
    """
    Detect frame and switch between Tx and Rx
    """
    def __init__(self, node_type):
        super().__init__()
        self.node_type = node_type
        # generate packed datas
        self.packed_datas: list[np.ndarray] = generate_packed_data()

    def run(self):
        global received_frames
        global all_buffer
        # init and run Tx and Rx
        tx = Tx()
        tx.start()
        rx = Rx()
        rx.start()
        start_time = time.time()
        if self.node_type == NodeType.TRANSMITTER:
            # send datas
            for i in range(TOTAL_FRAME_NUMBER):
                # put packed data into Tx frame and switch to Tx thread
                self.phy_send(i)
                # record sending time
                data_send_time[i] = time.time()
                print(f'Packed data {i}-th sent.')
                # check ack with a range
                if not (i + 1) % CHECK_ACK_RECEIVED_RANGE_SIZE:
                    self.check_ack_with_range(
                        i + 1 - CHECK_ACK_RECEIVED_RANGE_SIZE, i + 1)
            # sending finished
            print(
                f'Transmission finished, total time used: {time.time()-start_time}'
            )
        elif self.node_type == NodeType.RECEIVER:
            # point to where in coming data is processing
            curr_pointer = 0
            while received_frames < TOTAL_FRAME_NUMBER:
                while curr_pointer + DETECT_PREAMBLE_LENGTH > len(all_buffer):
                    # if current available buffer length doesn't reach detect try length, wait...
                    pass
                # find where preamble starts
                try_preamble_buffer = all_buffer[curr_pointer:curr_pointer+PREAMBLE_TRY_LENGTH]
                preamble_start_index = detect_preamble(try_preamble_buffer)
                if preamble_start_index is None:
                    # no preamble, go and check next
                    curr_pointer += PREAMBLE_TRY_LENGTH-len(PREAMBLE)
                    continue
                curr_pointer += preamble_start_index
                # wait till a whole frame received
                while curr_pointer+FRAME_DATA_LENGTH > len(all_buffer):
                    pass
                # switch to Rx and decode the frame
                Rx_frame[:] = all_buffer[curr_pointer:curr_pointer+FRAME_DATA_LENGTH]
                self.package_detected()
                curr_pointer += FRAME_DATA_LENGTH
            print(f'Receive finished, total time used: {time.time()-start_time}')
            # write to file bin
            write_received_date_to_bin()
        else:
            raise ValueError

    def phy_send(self, i):
        # PHYSend. MAC thread call this function to send one MAC frame.
        # The finishing of the transmission is notified by TX_DONE event.
        # send data through Tx_frame and clean it after send finished
        data = self.packed_datas[i]
        Tx_frame[:] = data[:]
        # turn to Tx status to transfer data
        self.Tx_pending()
        Tx_frame[:] = []

    @staticmethod
    def Tx_pending():
        global Tx_condition
        global MAC_condition
        Tx_condition.acquire()
        Tx_condition.notify()
        # turn to Tx status
        Tx_condition.release()
        MAC_condition.acquire()
        # release MAC_condition and wait to be notified by Tx
        MAC_condition.wait()

    @staticmethod
    def package_detected():
        # MAC thread detected a frame, turn to Rx decode
        Rx_condition.acquire()
        Rx_condition.notify()
        # turn to Rx status
        Rx_condition.release()
        MAC_condition.acquire()
        # release MAC_condition and wait to be notified by Rx
        MAC_condition.wait()

    @staticmethod
    def decode_ack(data):
        bits = np.zeros(8)
        for i in range(8):
            bits[i] = np.sum(data[i*BIT_SIGNAL_LENGTH:(i+1)*BIT_SIGNAL_LENGTH]*SIGNAL_ONE)
        return int(''.join([str(int(x)) for x in bits > 0]), 2)

    def check_ack_with_range(self, start, end):
        global retransmit_count
        curr_pointer = 0
        for i in range(start, end):
            while not ack_received_status[i]:
                # receive ack
                while len(all_buffer) - curr_pointer < PREAMBLE_TRY_LENGTH + ACK_LENGTH:
                    pass
                try_preamble_buffer = all_buffer[curr_pointer:curr_pointer + PREAMBLE_TRY_LENGTH]
                preamble_start_index = detect_preamble(try_preamble_buffer)
                if preamble_start_index is None:
                    # no preamble, go and check next
                    curr_pointer += PREAMBLE_TRY_LENGTH - len(PREAMBLE)
                else:
                    curr_pointer += preamble_start_index
                    ack = self.decode_ack(all_buffer[curr_pointer:curr_pointer + ACK_LENGTH])
                    if not ack_received_status[ack]:
                        print(f'ack {ack} received')
                        ack_received_status[ack] = True
                if time.time() - data_send_time[i] > retransmit_time:
                    retransmit_count[i] += 1
                    if retransmit_count[i] > max_retransmit:
                        print('link error')
                        sys.exit(-1)
                    else:
                        print(f'Resend data {i}')
                        self.phy_send(i)
                        data_send_time[i] = time.time()


class Tx(Thread):
    def run(self):
        """
        send packed data in Tx_frame
        """
        global output_index
        global node_status
        # wait to be wake up by MAC thread
        Tx_condition.acquire()
        Tx_condition.wait()
        node_status = NodeStatus.SENDING_DATA
        while True:
            while len(Tx_frame) > output_index:
                print('dff', output_index)
                # data is still sending
                node_status = NodeStatus.SENDING_DATA
            node_status = NodeStatus.IDLE
            # reset output index
            output_index = 0
            # issue TxDone and turn to FRAME_DETECT status
            self.Tx_done()
            # send next data, set status to SENDING_DATA
            node_status = NodeStatus.SENDING_DATA

    @staticmethod
    def Tx_done():
        # issue TxDone event and turn to FRAME_DETECT status
        MAC_condition.acquire()
        # wake up MAC thread
        MAC_condition.notify()
        # turn to MAC status
        MAC_condition.release()
        Tx_condition.acquire()
        # release Tx_condition and wait to be wakened by MAC
        Tx_condition.wait()


class Rx(Thread):
    def run(self):
        global received_frames
        global Rx_frame
        global node_status
        Rx_condition.acquire()
        Rx_condition.wait()
        while True:
            if not Rx_frame or len(Rx_frame) != FRAME_DATA_LENGTH:
                raise Exception('Rx_frame length not enough')
            decoded_bits = self.decode_to_bits(Rx_frame)
            if not CRC8_check(decoded_bits):
                print('CRC wrong')
            else:
                frame_index = int(decoded_bits[:8], 2)
                if frame_index < 0 or frame_index > TOTAL_FRAME_NUMBER:
                    raise Exception('wrong frame index')
                node_status = NodeStatus.SENDING_ACK
                print(f'Frame {frame_index} received.')
                if not frame_received_status[frame_index]:
                    frame_received_status[frame_index] = True
                    received_data[frame_index] = decoded_bits[8:len(decoded_bits)-8]
                    received_frames += 1
            Rx_frame = []
            self.Rx_done()

    @staticmethod
    def decode_to_bits(raw_data):
        bits = np.zeros(BITS_PER_FRAME+1)
        for i in range(BITS_PER_FRAME+1):
            bits[i] = np.sum(raw_data[i*BIT_SIGNAL_LENGTH:(i+1)*BIT_SIGNAL_LENGTH]*SIGNAL_ONE)
        return ''.join([str(int(x)) for x in bits > 0])

    @staticmethod
    def Rx_done():
        # issue RxDone event and turn to FRAME_DETECT status
        MAC_condition.acquire()
        # wake up MAC thread
        MAC_condition.notify()
        # turn to FRAME_DETECT status
        MAC_condition.release()
        Rx_condition.acquire()
        # release Rx_condition and wait to be wakened by MAC
        Rx_condition.wait()


def generate_packed_data() -> list[np.ndarray]:
    with open(input_file_name, 'rb') as f:
        raw_data = f.read()
    bit_data = ''.join(['{0:08b}'.format(x) for x in raw_data])
    packed_datas: list = []
    for i in range(TOTAL_FRAME_NUMBER):
        data = [PREAMBLE]
        frame_index: str = '{0:08b}'.format(i)
        payload: str = bit_data[BITS_PER_FRAME * i:BITS_PER_FRAME * (i + 1)]
        for bit in CRC8_encode([int(x) for x in frame_index + payload]):
            data.append(SIGNAL_ONE if bit == '1' else SIGNAL_ZERO)
        packed_datas.append(np.concatenate(data, dtype=np.float32))
    return packed_datas


def detect_preamble(data: np.ndarray):
    corr = np.correlate(data, PREAMBLE)
    if np.max(corr) > PREAMBLE_THRESHOLD:
        return np.argmax(corr)+len(PREAMBLE)
    return None


def init_stream():
    """init sounddevice stream"""
    # sd.default.extra_settings = sd.AsioSettings(channel_selectors=[0]), sd.AsioSettings(channel_selectors=[1])
    sd.default.device[0] = 2
    sd.default.device[1] = 3
    return sd.Stream(samplerate=F,
                     blocksize=BLOCK_SIZE,
                     channels=CHANNELS,
                     dtype=np.float32,
                     latency=LATENCY,
                     callback=callback
                     )


def callback(indata: ndarray, outdata: ndarray, frames: int, time, status) -> None:
    global all_buffer
    global output_index
    global ack_buffer
    global node_status
    # append all in coming data to all_buffer
    all_buffer = np.append(all_buffer, indata[:, 0])
    if node_status == NodeStatus.IDLE:
        outdata.fill(0)
    elif node_status == NodeStatus.SENDING_DATA:
        print(f'output index: {output_index}')
        # write data into outdata
        if len(Tx_frame) - output_index > frames:
            outdata[:] = np.asarray(Tx_frame[output_index:output_index + frames]).reshape(frames, 1)
        else:
            outdata[:] = np.append(
                Tx_frame[output_index:],
                np.zeros(frames - (len(Tx_frame) - output_index))).reshape(frames, 1)
        output_index += frames
    elif node_status == NodeStatus.SENDING_ACK:
        # generate next ack and put into outdata
        next_ack = generate_next_packed_ACK()
        outdata[:] = np.append(next_ack, np.zeros(frames - len(next_ack))).reshape(frames, 1)
        node_status = NodeStatus.IDLE


def generate_next_packed_ACK():
    """get next ACK"""
    global PREAMBLE
    global sending_ack_index
    # add preamble
    ack = [PREAMBLE]
    # add ACK index
    for bit in '{0:08b}'.format(sending_ack_index):
        ack.append(SIGNAL_ONE if int(bit) else SIGNAL_ZERO)
    # increase sending ack's index
    sending_ack_index += 1
    return ack