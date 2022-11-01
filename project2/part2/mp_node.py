from multiprocessing import Queue, Pipe, Process
from multiprocessing.connection import PipeConnection
from time import time
from typing import Any, Callable, Iterable
import queue as standard_queue


class LinkError(Exception):
    def __init__(self, msg: str):
        self.message = msg

    def __str__(self):
        return f'{self.message}: Link Error!'


class MAC(Process):
    def __init__(self, MAC_Tx_queue: Queue, MAC_Rx_queue: Queue,
                 MAC_Tx_pipe: PipeConnection) -> None:
        super().__init__()
        self.MAC_Tx_queue = MAC_Tx_queue
        self.MAC_Rx_queue = MAC_Rx_queue
        self.MAC_Tx_pipe = MAC_Tx_pipe

    def run(self):
        print('MAC runs')
        data_list = self.read_data()
        mac_frame_list = [self.gen_frame(payload) for payload in data_list]
        try:
            for idx, mac_frame in enumerate(mac_frame_list):
                self.MAC_Tx_queue.put(mac_frame, timeout=1)  #time out if 1s
                if not self.MAC_Tx_pipe.poll(1):  # wait for Tx_done
                    raise LinkError('MAC')

                # how about ACK?
        except standard_queue.Full:
            print('MAC:link error')
        except LinkError as e:
            print(e)

    def read_data(self):
        with open('./INPUT.bin', 'rb') as f:
            res = f.read()
            bit_stream = ''.join(
                ['{0:08b}'.format(x) for _, x in enumerate(res)])

        temp = [int(bit) for bit in bit_stream]
        return [temp[i:i + 100] for i in range(0, len(temp), 100)]

    def gen_frame(self,
                  payload: list[int],
                  frame_dest=0,
                  frame_src=0,
                  frame_seq: int = 0,
                  is_ACK=False):
        if not is_ACK:
            dest_with_src = [0 for _ in range(8)]
            frame_type = [0 for _ in range(4)]  #0000 for not ACK
            seq = [int(x) for x in '{0:08b}'.format(frame_seq)]
            return dest_with_src + frame_type + seq + payload
        else:
            pass


class Tx(Process):
    def __init__(self, MAC_Tx_queue: Queue,
                 Tx_MAC_pipe: PipeConnection) -> None:
        super().__init__()
        self.MAC_Tx_queue = MAC_Tx_queue
        self.Tx_MAC_pipe = Tx_MAC_pipe

    def run(self):
        print('Tx runs')
        try:
            while True:
                mac_frame = self.MAC_Tx_queue.get(timeout=1)
        except standard_queue.Empty:
            print('link error')


class Rx(Process):
    def __init__(self, MAC_Rx_queue: Queue) -> None:
        super().__init__()
        self.MAC_Rx_queue = MAC_Rx_queue

    def run(self) -> None:
        print('Rx runs')


def main():
    MAC_Tx_queue = Queue(maxsize=1)
    MAC_Rx_queue = Queue(maxsize=1)
    MAC_Tx_pipe, Tx_MAC_pipe = Pipe()
    mac = MAC(MAC_Tx_queue, MAC_Rx_queue, MAC_Tx_pipe)
    tx = Tx(MAC_Tx_queue, Tx_MAC_pipe)
    rx = Rx(MAC_Rx_queue)

    mac.start()
    tx.start()
    rx.start()


if __name__ == '__main__':
    main()