import time
from threading import Thread
from numpy import ndarray
import sounddevice as sd
from frame import *
from general import *
from globals import *


class PHY(Thread):
    """
    Detect frame and switch between Tx and Rx
    """

    def __init__(self):
        super().__init__()
        self.packed_datas: list[np.ndarray] = None

    def run(self):
        global incoming_MACs
        global incoming_MACs_handle_index
        global output_data_list
        global output_data_index
        global receive_frame_index
        global data_send_time

        global Rx_frame
        # init and run Tx and Rx
        tx = Tx()
        tx.start()
        rx = Rx()
        rx.start()
        listener = Listener()
        listener.start()
        # if there are data to be sent
        while True:
            if output_data_index != len(output_data_list):
                self.packed_datas = self.generate_packed_data(output_data_list[output_data_index])
                frame_num = len(self.packed_datas)
                self.reset_counts(frame_num)
                output_data_index += 1
                start_time = time.time()
                for i in range(frame_num):
                    # put packed data into Tx frame and switch to Tx thread
                    self.phy_send(i)
                    time.sleep(0.001)
                    # record sending time
                    data_send_time[i] = time.time()
                    print(f'Packed data {i}-th sent.')
                    # check ack with a range
                    if not (i + 1) % CHECK_ACK_RECEIVED_RANGE_SIZE:
                        self.check_ack_with_range(i + 1 - CHECK_ACK_RECEIVED_RANGE_SIZE, i + 1)
                self.check_ack_with_range(0, frame_num)
                # sending finished
                print(f'Transmission finished, total time used: {time.time() - start_time}')
            if incoming_MACs_handle_index != len(incoming_MACs):
                frame = incoming_MACs[incoming_MACs_handle_index]
                incoming_MACs_handle_index += 1
                receive_frame_index = frame.seq
                # switch to Rx and send ack
                self.package_detected()
                # write to file
                self.write_to_file(frame.payload)

    @staticmethod
    def put_01_data(data: str):
        global output_data_list
        output_data_list.append(data)

    @staticmethod
    def write_to_file(data):
        with open('output.txt', 'a') as f:
            f.write(data)

    @staticmethod
    def generate_packed_data(data: str) -> list[np.ndarray]:
        """
        args:
            data: 01 bit string
        """
        packed_datas: list = []
        for i in range(len(data) // PHY_DATA_PAYLOAD_LEN + 1):
            packed_data = [PREAMBLE]
            frame_index: str = '{0:08b}'.format(i)
            payload: str = data[PHY_DATA_PAYLOAD_LEN * i:PHY_DATA_PAYLOAD_LEN * (i + 1)]
            for bit in CRC8_encode(frame_index + payload):
                packed_data.append(SIGNAL_ONE if int(bit) else SIGNAL_ZERO)
            packed_datas.append(np.concatenate(packed_data, dtype=np.float32))
        return packed_datas

    def phy_send(self, i):
        # PHYSend. MAC thread call this function to send one MAC frame.
        # The finishing of the transmission is notified by TX_DONE event.
        # send data through Tx_frame and clean it after send finished
        global Tx_frame
        data = self.packed_datas[i]
        Tx_frame = data[:]
        # turn to Tx status to transfer data
        self.Tx_pending()
        Tx_frame = []

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
    def reset_counts(total_frame_num):
        """Reset retransmit count and ack received status
        """
        global retransmit_count
        global ack_received_status
        global data_send_time
        retransmit_count = [0] * total_frame_num
        ack_received_status = [False] * total_frame_num
        data_send_time = [0.0] * total_frame_num

    def check_ack_with_range(self, start, end):
        global retransmit_count
        global ack_received_status
        global incoming_acks
        global incoming_acks_handle_index
        global curr_pointer
        global data_send_time
        for i in range(start, end):
            while not ack_received_status[i]:
                while incoming_acks_handle_index != len(incoming_acks):
                    print(f'receive ack: {incoming_acks[incoming_acks_handle_index].seq}')
                    ack_received_status[incoming_acks[incoming_acks_handle_index].seq] = True
                    incoming_acks_handle_index += 1
                if not ack_received_status[i]:
                    if time.time() - data_send_time[i] > RETRANSMIT_TIME:
                        retransmit_count[i] += 1
                        if retransmit_count[i] > MAX_RETRANSMIT:
                            print('link error')
                            exit(-1)
                        else:
                            print(f'Resend data {i}')
                            self.phy_send(i)
                            data_send_time[i] = time.time()


class Tx(Thread):
    def run(self):
        """
        send packed data in Tx_frame
        """
        global sd_output_index
        global node_status
        # wait to be wake up by MAC thread
        Tx_condition.acquire()
        Tx_condition.wait()
        node_status = NodeStatus.SENDING_DATA
        while True:
            while len(Tx_frame) > sd_output_index:
                # data is still sending
                node_status = NodeStatus.SENDING_DATA
            node_status = NodeStatus.IDLE
            # reset output index
            sd_output_index = 0
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
        global receive_frame_index
        global node_status
        Rx_condition.acquire()
        Rx_condition.wait()
        while True:
            send_ACK(receive_frame_index)
            node_status = NodeStatus.SENDING_ACK
            print(f'Frame {receive_frame_index} received, send ack {receive_frame_index}')
            self.Rx_done()

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


class Listener(Thread):
    """Detect preamble and add to incoming MAC data or ack list
    根据PHY frame中的Len字段来判断frame是一个data还是ack
    """

    def run(self):
        global incoming_MACs
        global incoming_acks
        global all_buffer
        # processing index of all_buffer
        curr_processing = 0
        while True:
            while curr_processing + PREAMBLE_TRY_LENGTH > len(all_buffer):
                # wait for detectable preamble try length
                pass
            try_preamble_buffer = all_buffer[curr_processing:curr_processing + PREAMBLE_TRY_LENGTH]
            preamble_end_index = self.detect_preamble(try_preamble_buffer)
            if preamble_end_index is None:
                # no preamble, go and check next
                curr_processing += PREAMBLE_TRY_LENGTH - len(PREAMBLE) - 10
                continue
            curr_processing += preamble_end_index
            # wait till a whole MAC frame received
            while curr_processing + (PHY_FRAME_LEN - PREAMBLE_LEN) * BIT_LEN > len(all_buffer):
                pass
            # get PHY Len(MAC frame len) field bit
            mac_frame_len = int(self.decode_to_bits(all_buffer[curr_processing:curr_processing + LEN_LEN * BIT_LEN]), 2)
            curr_processing += LEN_LEN * BIT_LEN
            raw_frame_len = (mac_frame_len + CRC_LEN) * BIT_LEN
            decoded_bits = self.decode_to_bits(all_buffer[curr_processing:curr_processing + raw_frame_len])
            if not CRC8_check(decoded_bits):
                print('CRC wrong')
                continue
            if raw_frame_len == PHY_ACK_PAYLOAD_LEN:
                # ack
                incoming_acks.append(MacFrame(decoded_bits))
            else:
                # data
                incoming_MACs.append(MacFrame(decoded_bits))
            curr_processing += raw_frame_len

    @staticmethod
    def detect_preamble(data: np.ndarray):
        corr = np.correlate(data, PREAMBLE)
        if np.max(corr) > PREAMBLE_THRESHOLD:
            return np.argmax(corr) + len(PREAMBLE)
        return None

    @staticmethod
    def get_one_bit(data: np.ndarray):
        return int(np.sum(data * SIGNAL_ONE) > 0)

    def decode_to_bits(self, raw_data):
        bits = [0] * (len(raw_data) // BIT_LEN)
        for i in range(len(bits)):
            bits[i] = self.get_one_bit(raw_data[i * BIT_LEN:(i + 1) * BIT_LEN])
        return ''.join(bits)


def init_stream():
    """init sounddevice stream"""
    # sd.default.extra_settings = sd.AsioSettings(channel_selectors=[0]), sd.AsioSettings(channel_selectors=[1])
    sd.default.device[0] = 4
    sd.default.device[1] = 4
    return sd.Stream(samplerate=F,
                     blocksize=BLOCK_SIZE,
                     channels=CHANNELS,
                     dtype=np.float32,
                     latency=LATENCY,
                     callback=callback
                     )


def callback(indata: ndarray, outdata: ndarray, frames: int, time, status) -> None:
    global all_buffer
    global sd_output_index
    global ack_buffer
    global node_status
    # append all in coming data to all_buffer
    all_buffer = np.append(all_buffer, indata[:, 0])
    if node_status == NodeStatus.IDLE:
        outdata.fill(0)
    elif node_status == NodeStatus.SENDING_DATA:
        # write data into outdata
        try:
            if len(Tx_frame) - sd_output_index > frames:
                outdata[:] = np.asarray(Tx_frame[sd_output_index:sd_output_index + frames]).reshape(frames, 1)
            else:
                outdata[:] = np.append(
                    np.asarray(Tx_frame[sd_output_index:]),
                    np.zeros(frames - (len(Tx_frame) - sd_output_index))).reshape(frames, 1)
            sd_output_index += frames
        except Exception:
            print(f'err: len Tx frame:{len(Tx_frame)}')
    elif node_status == NodeStatus.SENDING_ACK:
        # generate next ack and put into outdata
        outdata[:] = np.append(ack_buffer[:], np.zeros(frames - len(ack_buffer))).reshape(frames, 1)
        node_status = NodeStatus.IDLE
        ack_buffer = []


def send_ACK(n):
    global PREAMBLE
    global ack_buffer
    # add preamble
    ack = [PREAMBLE]
    # add ACK index
    for bit in '{0:08b}'.format(n):
        ack.append(SIGNAL_ONE if int(bit) else SIGNAL_ZERO)
    ack_buffer = np.concatenate([ack_buffer, np.concatenate(ack)])
