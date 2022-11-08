from multiprocessing import Queue, Pipe, Process, Barrier
from multiprocessing.synchronize import Barrier as Barrier_
from multiprocessing.connection import PipeConnection
import time
from typing import Any, Callable, Iterable
import queue as standard_queue
import sounddevice as sd
from utils import gen_Mac_frame, gen_PHY_frame, f, read_data, CHUNK, extract_PHY_frame, extract_MAC_frame, get_ACK_id, DUMMY


class LinkError(Exception):
    def __init__(self, msg: str):
        self.message = msg

    def __str__(self):
        return f'{self.message}: Link Error!'


def print_start(msg: str = ''):
    print('transmittion starts')


class MAC(Process):
    def __init__(self, Network_Link_queue: Queue,
                 Link_Network_queue: Queue) -> None:
        super().__init__()
        self.barrier = Barrier(3, print_start)
        self.Network_Link_queue = Network_Link_queue
        self.Link_Network_queue = Link_Network_queue
        self.MAC_Tx_pipe, self.Tx_MAC_pipe = Pipe()
        self.MAC_Tx_queue = Queue(maxsize=1)
        self.MAC_Rx_pipe, self.Rx_MAC_pipe = Pipe()
        self.MAC_Rx_queue = Queue(maxsize=10)
        self.cur_idx = 0

    def run(self):
        # self.temp = 1
        self.tx = Tx(self.MAC_Tx_queue, self.Tx_MAC_pipe, self.barrier)
        self.rx = Rx(self.MAC_Rx_queue, self.Rx_MAC_pipe, self.barrier)
        self.tx.start()
        self.rx.start()
        print('MAC runs. Waiting for Tx and Rx...')
        self.barrier.wait()
        try:
            while True:
                if not self.Network_Link_queue.empty():
                    # if False:
                    self.cur_idx += 1
                    payload = self.Network_Link_queue.get()
                    # payload = [1 for _ in range(100)]
                    # print(f'取得payload:{payload}')
                    # mac_frame = gen_Mac_frame(payload, frame_seq=self.cur_idx)
                    mac_frame = gen_Mac_frame(payload, frame_seq=self.cur_idx)
                    # If MAC did not recieve an ACK in a given time slot, then it should resend this current frame.
                    # If the times of resending surpass a threshhold, then we can say Link Error
                    for i in range(12):
                        self.MAC_Tx_queue.put(mac_frame)
                        self.MAC_Tx_pipe.recv()
                        if self.MAC_Rx_pipe.poll(0.5):
                            ack: str = self.MAC_Rx_pipe.recv(
                            )  # receive an ACK like 'ACK_10'
                            print('收到了ACK')
                            ack_idx = int(ack.split('_')[-1])
                            if ack_idx != self.cur_idx:
                                continue
                            else:  # means that we get the correct ACK
                                print('ACK确认')
                                break
                    else:  # this means that surpassing the threashhold, raise Link Error
                        raise LinkError('MAC')
                if not self.MAC_Rx_queue.empty():
                    mac_frame = self.MAC_Rx_queue.get()
                    ack_frame = gen_Mac_frame(is_ACK=True,
                                              mac_frame_received=mac_frame)
                    print('发送了ACK')
                    self.MAC_Tx_queue.put(ack_frame)
                    # if it is correct, put this to Link_MAC_queue for store
                    self.Link_Network_queue.put(mac_frame)
                    pass
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
    def __init__(self, MAC_Tx_queue: Queue, Tx_MAC_pipe: PipeConnection,
                 barrier: Barrier_) -> None:
        super().__init__()
        self.MAC_Tx_queue = MAC_Tx_queue
        self.Tx_MAC_pipe = Tx_MAC_pipe
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
                mac_frame = self.MAC_Tx_queue.get_nowait()
                # print(f'正在发送mac_frame: {mac_frame}')
                print(len(mac_frame))
                phy_frame = gen_PHY_frame(mac_frame)
                # print(len(phy_frame))
                self.stream.write(phy_frame.tobytes())
                self.Tx_MAC_pipe.send('Tx Done')
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
                        print(f'ACK:{ACK_id}')
                        self.Rx_MAC_pipe.send(f'ACK_{ACK_id}')

                    else:
                        print('收到了一个frame')
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
            Network_Link_queue.put(data, timeout=8)
            if idx == 0:
                break
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
            recv_list = recv_list + Link_Network_queue.get(timeout=8)

    except standard_queue.Empty:
        print('transmittion finished! Start storing')
        # mac.terminate()
        with open('./OUTPUT.txt', 'w') as f:
            f.writelines(map(lambda x: str(x), recv_list))

        print('Writing to disk finished!')
        # mac.terminate()


if __name__ == '__main__':
    # main()
    main2()
