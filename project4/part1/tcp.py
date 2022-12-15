from multiprocessing import Process, Manager, Event, Queue
from threading import Thread
from dataclasses import dataclass
from queue import Queue as _Queue
from network import NETWORK, D_ADDR, TRAN_NET_ITEM
from tcp_utils import SOCKET, gen_tcp_packet, get_tcp_s_port, get_tcp_payload


@dataclass
class TCP_ITEM:
    d_addr: D_ADDR = None
    seq: int = 0
    is_connected: bool = False
    is_closed: bool = True
    t_queue: _Queue[bytes] = None  # send data
    r_queue: _Queue[bytes] = None  #recv data


class T_THREAD(Thread):
    def __init__(self, tcp_table: dict[str, TCP_ITEM],
                 Transport_Network_queue: 'Queue[TRAN_NET_ITEM]') -> None:
        self.tcp_table = tcp_table
        self.Transport_Network_queue = Transport_Network_queue
        super().__init__()

    def run(self):
        while True:
            for key in self.tcp_table.keys():
                tcp_item = self.tcp_table[key]
                if not tcp_item.t_queue.empty():
                    tcp_packet = gen_tcp_packet()
                    self.Transport_Network_queue.put_nowait(
                        TRAN_NET_ITEM(1, tcp_item.d_addr, tcp_packet, 'TCP'))


class R_THREAD(Thread):
    def __init__(self, Network_Transport_queue: 'Queue[bytes]',
                 tcp_table: dict[str, TCP_ITEM]) -> None:
        self.Network_Transport_queue = Network_Transport_queue
        self.tcp_table = tcp_table
        super().__init__()

    def run(self):
        if not self.Network_Transport_queue.empty():
            tcp_packet = self.Network_Transport_queue.get_nowait()
            tcp_port = get_tcp_s_port(tcp_packet)
            tcp_payload = get_tcp_payload(tcp_packet)
            self.tcp_table[str(tcp_port)].r_queue.put_nowait(tcp_payload)


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
        self.tcp_table[str(port)].is_connected = True

    def read(self, _socket: SOCKET):
        port = _socket.port
        tcp_item = self.tcp_table[str(port)]
        while (not tcp_item.is_closed()) or (not tcp_item.r_queue.empty()):
            if not tcp_item.r_queue.empty():
                return tcp_item.r_queue.get_nowait()

        return -1

    def write(self, _socket: SOCKET, data: bytes):
        port = _socket.port
        tcp_item = self.tcp_table[str(port)]
        if tcp_item.is_connected:
            tcp_item.t_queue.put_nowait(data)
            return 1

        return -1


if __name__ == '__main__':
    print('fs')