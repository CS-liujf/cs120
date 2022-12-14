from multiprocessing import Process, Manager, Event, Queue
from threading import Thread
from dataclasses import dataclass
from queue import Queue as _Queue
from network import NETWORK, D_ADDR, TRAN_NET_ITEM


@dataclass
class TCP_ITEM:
    d_addr: D_ADDR = None
    is_connected: bool = False
    is_closed: bool = True
    t_queue: _Queue[bytes] = None  # send data
    r_queue: _Queue[bytes] = None  #recv data


class T_THREAD(Thread):
    def __init__(self) -> None:
        super().__init__()


class R_THREAD(Thread):
    def __init__(self) -> None:
        super().__init__()


class TCP(Process):
    def __init__(self) -> None:
        self.tcp_table: dict[str, TCP_ITEM] = Manager().dict()
        self.event = Event()
        # self.Transport_Network_queue: Queue[bytes] = Queue()
        # self.Network_Transport_queue: Queue[bytes] = Queue()
        super().__init__()

    def run(self) -> None:
        Transport_Network_queue: Queue[TRAN_NET_ITEM] = Queue()
        Network_Transport_queue: Queue[bytes] = Queue()
        network = NETWORK(Transport_Network_queue, Network_Transport_queue)
        network.start()
        while not self.event.is_set():
            pass

    def bind(self, port: int):
        if str(port) in self.tcp_table:
            print('error: Address already in use')
        self.tcp_table[str(port)] = 1

    def connect(self, d_addr: D_ADDR, port: int = None):
        #three way handshake
        self.tcp_table[str(port)].d_addr = d_addr


if __name__ == '__main__':
    print('fs')