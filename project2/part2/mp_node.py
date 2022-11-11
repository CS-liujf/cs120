from multiprocessing import Queue, Pipe, Process, Barrier
from multiprocessing.synchronize import Barrier as Barrier_
from multiprocessing.connection import PipeConnection
from threading import Thread
import time
from typing import NamedTuple
import queue as standard_queue
import sounddevice as sd
from utils import gen_Mac_frame, gen_PHY_frame, f, read_data, CHUNK, extract_PHY_frame, extract_MAC_frame, get_ACK_id, DUMMY
from dataclasses import dataclass


class LinkError(Exception):
    def __init__(self, msg: str):
        self.message = msg

    def __str__(self):
        return f'{self.message}: Link Error!'


def print_start(msg: str = ''):
    print('transmittion starts')


@dataclass
class TWINDOW_ITEM:
    seq: int = None
    data: list[int] = None
    time: float = None
    ACK_flag: bool = False
    re_count: int = 0


class MAC_Tx_Item(NamedTuple):
    seq: int
    data: list[int]


class Tx_Message(NamedTuple):
    seq: int
    time: float


class TWINDOW(Thread):
    def __init__(self, capacity: int, max_seq_num: int,
                 Network_Link_queue: Queue, MAC_Tx_queue: 'Queue[MAC_Tx_Item]',
                 Tx_message_queue: 'Queue[Tx_Message]', Rx_ACK_queue: Queue,
                 barrier: Barrier_):
        self.capacity = capacity
        self.size = 0
        self.seq = 0
        self.max_seq_num = max_seq_num
        self.count = 0  # for checing link error
        self.Network_Link_queue = Network_Link_queue
        self.MAC_Tx_queue = MAC_Tx_queue
        self.Tx_message_queue = Tx_message_queue
        self.Rx_ACK_queue = Rx_ACK_queue
        self.window: list[TWINDOW_ITEM] = [
            TWINDOW_ITEM() for _ in range(self.capacity)
        ]
        self.barrier = barrier
        super().__init__()

    def run(self):
        self.barrier.wait()
        while True:
            self.check_ACK()
            self.check_Tx_message()
            self.check_time()
            self.put_data()

    def put_data(self):
        if self.size < self.capacity and (not self.Network_Link_queue.empty()):
            data = self.Network_Link_queue.get_nowait()
            seq = self.seq
            self.window[self.size].data = data
            self.window[self.size].seq = seq
            self.size = self.size + 1
            self.seq = (self.seq + 1) % self.max_seq_num
            self.MAC_Tx_queue.put_nowait(MAC_Tx_Item(seq, data))

    def check_Tx_message(self):
        if not self.Tx_message_queue.empty():
            tx_message = self.Tx_message_queue.get_nowait()
            # print(f'tx_message {tx_message}')
            for idx, item in enumerate(self.window):
                if item.seq == tx_message.seq and item.ACK_flag == False:
                    self.window[idx].time = tx_message.time
                    break

        max_re_count = max(map(lambda x: x.re_count, self.window))

        if max_re_count > 10:
            raise LinkError('MAC')

    def check_ACK(self):
        if not self.Rx_ACK_queue.empty():
            seq = self.Rx_ACK_queue.get_nowait()
            for idx, item in enumerate(self.window):
                if item.seq == seq:
                    self.window[idx].ACK_flag = True
                    # check wether this window can move
                    check_flag = map(lambda x: x.ACK_flag,
                                     self.window[:idx + 1])
                    print(check_flag)
                    if all(check_flag):
                        del self.window[:idx + 1]
                        self.window = self.window + [
                            TWINDOW_ITEM() for _ in range(idx + 1)
                        ]
                        self.size = self.size - (idx + 1)
                    break

    def check_time(self):
        count = 0
        for idx, item in enumerate(self.window):
            if (item.time != None) and (item.ACK_flag == False):
                t = time.time()
                if (t - item.time) > 2:
                    print(
                        f'超时重发, item_seq: {item.seq}, item_time: {item.time}, time_now:{t}'
                    )
                    # resend
                    # print(f'check_time超时: {idx}')
                    self.window[idx].re_count += 1
                    self.MAC_Tx_queue.put_nowait(
                        MAC_Tx_Item(item.seq, item.data))
                    # self.window[idx].time = t
                    count += 1

        # print(f'count: {count}')


class RWINDOW(Thread):
    def __init__(self,
                 size: int,
                 max_seq_num: int,
                 Network_Link_queue: Queue,
                 MAC_Tx_queue: Queue,
                 Rx_ACK_queue: Queue = None):
        self.size = size
        self.Network_Link_queue = Network_Link_queue
        self.MAC_Tx_queue = MAC_Tx_queue
        self.Rx_ACK_queue = Rx_ACK_queue
        self.window = [None for _ in range(self.size)]
        super().__init__()

    def run(self):
        while True:
            pass


class MAC(Process):
    def __init__(self, Network_Link_queue: Queue,
                 Link_Network_queue: Queue) -> None:
        super().__init__()
        self.barrier = Barrier(4, print_start)
        self.Network_Link_queue = Network_Link_queue
        self.Link_Network_queue = Link_Network_queue
        self.MAC_Tx_pipe, self.Tx_MAC_pipe = Pipe()
        self.MAC_Tx_queue: Queue[MAC_Tx_Item] = Queue()
        self.Tx_message_queue: Queue[Tx_Message] = Queue()
        self.Rx_ACK_queue = Queue()
        self.MAC_Rx_pipe, self.Rx_MAC_pipe = Pipe()
        self.MAC_Rx_queue = Queue()
        self.cur_idx = 0

    def run(self):
        # self.temp = 1
        self.tx = Tx(self.MAC_Tx_queue, self.Tx_message_queue, self.barrier)
        self.rx = Rx(self.MAC_Rx_queue, self.Rx_MAC_pipe, self.barrier)
        self.tw = TWINDOW(10, 16, self.Network_Link_queue, self.MAC_Tx_queue,
                          self.Tx_message_queue, self.Rx_ACK_queue,
                          self.barrier)
        self.tw.start()
        self.tx.start()
        self.rx.start()
        print('MAC runs. Waiting for Tx and Rx...')
        self.barrier.wait()
        try:
            self.tw.join()
        except LinkError as e:
            print(e)

        self.close_Tx_and_Rx()

    def close_Tx_and_Rx(self):
        self.tx.terminate()
        self.rx.terminate()

    def terminate(self) -> None:
        # print(self.temp)
        self.tx.terminate()
        self.rx.terminate()
        return super().terminate()


class Tx(Process):
    def __init__(self, MAC_Tx_queue: 'Queue[MAC_Tx_Item]',
                 Tx_Message_queue: 'Queue[Tx_Message]',
                 barrier: Barrier_) -> None:
        super().__init__()
        self.MAC_Tx_queue = MAC_Tx_queue
        self.Tx_Message_queue = Tx_Message_queue
        self.barrier = barrier

    def run(self):
        import pyaudio
        self.stream = pyaudio.PyAudio().open(format=pyaudio.paFloat32,
                                             rate=f,
                                             output=True,
                                             channels=1,
                                             frames_per_buffer=1)
        print('Tx runs')
        self.barrier.wait()
        # count = 0
        t1 = time.time()
        while True:
            if not self.MAC_Tx_queue.empty():
                mac_tx_item = self.MAC_Tx_queue.get_nowait()
                # print(f'正在发送mac_frame: {mac_frame}')
                mac_frame = gen_Mac_frame(mac_tx_item.data,
                                          frame_seq=mac_tx_item.seq)
                phy_frame = gen_PHY_frame(mac_frame)
                # print(len(phy_frame))
                self.stream.write(phy_frame.tobytes())
                t = time.time()
                self.Tx_Message_queue.put(Tx_Message(mac_tx_item.seq, t))
                print(f'发送了一个frame: {mac_tx_item.seq}, 时间: {t}')
            else:
                self.stream.write(DUMMY.tobytes())
            # count += 1
            # print(count)


class Rx(Process):
    def __init__(self, MAC_Rx_queue: Queue, Rx_MAC_pipe: PipeConnection,
                 barrier: Barrier_) -> None:
        super().__init__()
        self.MAC_Rx_queue = MAC_Rx_queue
        self.Rx_MAC_pipe = Rx_MAC_pipe
        self.barrier = barrier

    def run(self) -> None:
        import pyaudio
        self.stream = pyaudio.PyAudio().open(format=pyaudio.paFloat32,
                                             rate=f,
                                             input=True,
                                             channels=1,
                                             frames_per_buffer=1)
        print('Rx runs')
        self.barrier.wait()
        while True:
            # print('test')
            stream_data = self.stream.read(CHUNK)
            # print('读取了一个frame')
            if (phy_frame := extract_PHY_frame(stream_data)) is not None:
                # check CRC8 in extract_MAC_frame
                print('提取到phy_frame')
                if (mac_frame := extract_MAC_frame(phy_frame)) is not None:
                    # chech whther it is an ACK
                    if (ACK_id := get_ACK_id(mac_frame)) > 0:
                        self.Rx_MAC_pipe.send(f'ACK_{ACK_id}')

                    else:
                        self.MAC_Rx_queue.put(mac_frame)


def main():
    Network_Link_queue = Queue(maxsize=10)
    Link_Network_queue = Queue(maxsize=10)
    # Link_Network_queue=
    data_list = read_data()
    mac = MAC(Network_Link_queue, Link_Network_queue)
    mac.start()
    # frame transfered from Network layer to Link layer
    time.sleep(1)
    try:
        for idx, data in enumerate(data_list):
            Network_Link_queue.put(data, timeout=20)
        else:
            print('transmittion end')
        # while True:
        # Network_Link_queue.put([1 for _ in range(100)])
        # pass
    except:
        print('Network timeout!')


def main2():
    Network_Link_queue = Queue(maxsize=10)
    Link_Network_queue = Queue(maxsize=10)
    # Link_Network_queue=
    # data_list = read_data()
    mac = MAC(Network_Link_queue, Link_Network_queue)
    mac.start()
    recv_list = []
    try:
        while True:
            recv_list = recv_list + Link_Network_queue.get(timeout=12)

    except standard_queue.Empty:
        print('transmittion finished! Start storing')
        # mac.terminate()
        with open('./OUTPUT.txt', 'w') as f:
            f.writelines(map(lambda x: str(x), recv_list))

        print('Writing to disk finished!')
        # mac.terminate()


if __name__ == '__main__':
    main()
    # main2()
    # q = Queue()
    # q.put(12)
    # q.put(13)
    # print(q.get())
    # print(q.qsize())
    # print(q.get())
