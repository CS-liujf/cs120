from multiprocessing import Queue, Pipe, Process
from multiprocessing.connection import PipeConnection
import time
from typing import Any, Callable, Iterable
import queue as standard_queue
import sounddevice as sd
from utils import gen_PHY_frame, f, read_data


class LinkError(Exception):
    def __init__(self, msg: str):
        self.message = msg

    def __str__(self):
        return f'{self.message}: Link Error!'


class MAC(Process):
    def __init__(self, ) -> None:
        super().__init__()
        MAC_Tx_queue = Queue(maxsize=1)
        MAC_Rx_queue = Queue(maxsize=10)
        MAC_Tx_pipe, Tx_MAC_pipe = Pipe()
        self.MAC_Tx_queue = MAC_Tx_queue
        self.MAC_Rx_queue = MAC_Rx_queue
        self.MAC_Tx_pipe = MAC_Tx_pipe
        self.Tx_MAC_pipe = Tx_MAC_pipe
        self.MAC_Rx_pipe, self.Rx_MAC_pipe = Pipe()

    def run(self):
        print('MAC runs')
        self.tx = Tx(self.MAC_Tx_queue, self.Tx_MAC_pipe)
        self.rx = Rx(self.MAC_Rx_queue, self.Rx_MAC_pipe)
        self.tx.start()
        self.rx.start()
        data_list = read_data()
        mac_frame_list = [self.gen_frame(payload) for payload in data_list]
        try:
            for idx, mac_frame in enumerate(mac_frame_list):

                # how about ACK?
                # If MAC did not recieve an ACK in a given time slot, then it should resend this current frame.
                # If the times of resending surpass a threshhold, then we can say Link Error
                for i in range(6):
                    self.MAC_Tx_queue.put(mac_frame)
                    self.MAC_Tx_pipe.recv()
                    if self.MAC_Rx_pipe.poll(1):
                        # this means that we receive ACK
                        break
                else:  # this means that surpassing the threashhold, raise Link Error
                    raise LinkError('MAC')

        except standard_queue.Full as e:
            print(f'.MAC:link error occurs while sending')
        except LinkError as e:
            print(e, end='')
            print(f'在发送{idx} frame')

        # 添加判断，如果有数据要收，则从Rx中取数据并写入self.store_data中

        self.tx.terminate()
        self.rx.terminate()

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

    def terminate(self) -> None:
        self.tx.terminate()
        self.rx.terminate()
        return super().terminate()


class Tx(Process):
    def __init__(self, MAC_Tx_queue: Queue,
                 Tx_MAC_pipe: PipeConnection) -> None:
        super().__init__()
        self.MAC_Tx_queue = MAC_Tx_queue
        self.Tx_MAC_pipe = Tx_MAC_pipe

    def run(self):
        print('Tx runs')
        count = 0
        try:
            t1 = time.time()
            with sd.Stream(samplerate=48000, channels=1, dtype='float32') as f:
                while mac_frame := self.MAC_Tx_queue.get():
                    phy_frame = gen_PHY_frame(mac_frame)
                    f.write(phy_frame)
                    count += 1
                    self.Tx_MAC_pipe.send('Tx Done')
                    # if count % 100 == 0:
                    print(count)
        except standard_queue.Empty:
            t2 = time.time()
            print(f'Tx time:{t2-t1}')
            print('link error')


class Rx(Process):
    def __init__(self, MAC_Rx_queue: Queue,
                 Rx_MAC_pipe: PipeConnection) -> None:
        super().__init__()
        self.MAC_Rx_queue = MAC_Rx_queue
        self.Rx_MAC_pipe = Rx_MAC_pipe

    def run(self) -> None:
        print('Rx runs')
        while True:
            pass
            #这里要时刻监听收到的数据，并判断是否为ACK，若为ACK则调用self.Rx_MAC_pipe.send('Receive ACK')
            #若是正常数据则调用sel.MAC_Rx_queue.put(data)

        # with sd.InputStream(samplerate=f):
        #     while True:
        #         pass


def main():
    # MAC_Tx_queue = Queue(maxsize=1)
    # MAC_Rx_queue = Queue(maxsize=1)
    # MAC_Tx_pipe, Tx_MAC_pipe = Pipe()
    # mac = MAC(MAC_Tx_queue, MAC_Rx_queue, MAC_Tx_pipe)
    # tx = Tx(MAC_Tx_queue, Tx_MAC_pipe)
    # rx = Rx(MAC_Rx_queue)

    # mac.start()
    # tx.start()
    # rx.start()

    # t1 = time.time()
    # mac.join()
    # tx.join()
    # rx.join()
    # t2 = time.time()
    # print(t2 - t1)
    mac = MAC()
    mac.start()
    mac.join()


if __name__ == '__main__':
    main()
