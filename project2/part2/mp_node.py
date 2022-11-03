from multiprocessing import Queue, Pipe, Process, Barrier
from multiprocessing.synchronize import Barrier as Barrier_
from multiprocessing.connection import PipeConnection
import time
from typing import Any, Callable, Iterable
import queue as standard_queue
import sounddevice as sd
from utils import gen_PHY_frame, f, read_data, CHUNK, extract_PHY_frame, extract_MAC_frame, get_ACK_id


class LinkError(Exception):
    def __init__(self, msg: str):
        self.message = msg

    def __str__(self):
        return f'{self.message}: Link Error!'


def print_start(msg: str = ''):
    print('transmittion starts')


class MAC(Process):
    def __init__(self, Network_Link_queue: Queue) -> None:
        super().__init__()
        self.barrier = Barrier(3, print_start)
        self.Network_Link_queue = Network_Link_queue
        self.MAC_Tx_pipe, self.Tx_MAC_pipe = Pipe()
        self.MAC_Tx_queue = Queue(maxsize=1)
        self.MAC_Rx_pipe, self.Rx_MAC_pipe = Pipe()
        self.MAC_Rx_queue = Queue(maxsize=10)
        self.cur_idx = 0

    def run(self):
        self.tx = Tx(self.MAC_Tx_queue, self.Tx_MAC_pipe, self.barrier)
        self.rx = Rx(self.MAC_Rx_queue, self.Rx_MAC_pipe, self.barrier)
        self.tx.start()
        self.rx.start()
        print('MAC runs. Waiting for Tx and Rx...')
        self.barrier.wait()
        try:
            while True:
                if not self.Network_Link_queue.empty():
                    self.cur_idx += 1
                    payload = self.Network_Link_queue.get()
                    mac_frame = self.gen_Mac_frame(payload,
                                                   frame_seq=self.cur_idx)
                    # If MAC did not recieve an ACK in a given time slot, then it should resend this current frame.
                    # If the times of resending surpass a threshhold, then we can say Link Error
                    for i in range(6):
                        self.MAC_Tx_queue.put(mac_frame)
                        self.MAC_Tx_pipe.recv()
                        if self.MAC_Rx_pipe.poll(1):
                            #in fact we should check this ACK because maybe it is not corresponding to the current Id
                            # but now, since we transmit only one frame, this check can obmitted.
                            # this means that we receive ACK
                            ack: str = self.MAC_Rx_pipe.recv(
                            )  # receive an ACK like 'ACK_10'
                            ack_idx = int(ack.split('_')[-1])
                            if ack_idx != self.cur_idx:
                                continue
                            else:  # means that we get the correct ACK
                                break
                    else:  # this means that surpassing the threashhold, raise Link Error
                        raise LinkError('MAC')
                if not self.MAC_Rx_queue.empty():
                    ## do receive (may be write to disk ) and reply ACK
                    mac_frame = self.MAC_Rx_queue.get()
                    #check whether it is correct. If not, then we don't reply ACK. other wise put a ACK frame to the MAC_Tx_queue
                    # check
                    ack_frame = self.gen_Mac_frame([-1 for _ in range(100)],
                                                   is_ACK=True)
                    self.MAC_Tx_queue.put(ack_frame)
                    # if it is correct, put this to MAC_IP_queue for store
                    pass
        except LinkError as e:
            print(e)

        self.close_Tx_and_Rx()

    def close_Tx_and_Rx(self):
        self.tx.terminate()
        self.rx.terminate()

    @classmethod
    def get_seq_num():
        pass

    @classmethod
    def gen_Mac_frame(self,
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
            mac_frame = self.MAC_Tx_queue.get()
            phy_frame = gen_PHY_frame(mac_frame)
            # print(len(phy_frame))
            self.stream.write(phy_frame.tobytes())
            self.Tx_MAC_pipe.send('Tx Done')
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
            stream_data = self.stream.read(CHUNK)
            if (phy_frame := extract_PHY_frame(stream_data)) is not None:
                if (mac_frame := extract_MAC_frame(phy_frame)) is not None:
                    # chech whther it is an ACK
                    if (ACK_id := get_ACK_id(mac_frame)) > 0:
                        self.Rx_MAC_pipe.send(f'ACK_{ACK_id}')

                    else:
                        self.MAC_Rx_queue.put(mac_frame)
            #这里要时刻监听收到的数据，并判断是否为ACK，若为ACK则调用self.Rx_MAC_pipe.send('Receive ACK')
            #若是正常数据则调用sel.MAC_Rx_queue.put(data)


def main():
    Network_Link_queue = Queue(maxsize=10)
    # Link_Network_queue=
    data_list = read_data()
    mac = MAC(Network_Link_queue)
    mac.start()
    # frame transfered from Network layer to Link layer
    time.sleep(1)
    try:
        for idx, data in enumerate(data_list):
            Network_Link_queue.put(data, timeout=8)
        else:
            print('transmittion end')
    except:
        print('Network timeout!')


if __name__ == '__main__':
    main()
