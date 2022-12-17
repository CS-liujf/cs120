from multiprocessing import Process, Manager, Event, Queue, Barrier
from multiprocessing.synchronize import Barrier as Barrier_
from dataclasses import dataclass
from queue import Queue as _Queue
from network import NETWORK, TRAN_NET_ITEM
from tcp_utils import SOCKET, D_ADDR, gen_tcp_packet, get_tcp_d_port, get_tcp_payload


@dataclass
class TCP_ITEM:
    socket: SOCKET = None
    d_addr: D_ADDR = None
    seq: int = 0
    is_connected: bool = False
    is_closed: bool = True
    t_buffer: bytes = b''  # send data
    r_buffer: bytes = b''  #recv data


class T_PROCESS(Process):
    def __init__(self, tcp_table: dict[str, TCP_ITEM],
                 Transport_Network_queue: 'Queue[TRAN_NET_ITEM]') -> None:
        self.tcp_table = tcp_table
        self.Transport_Network_queue = Transport_Network_queue
        super().__init__()

    def run(self):
        while True:
            for key in self.tcp_table.keys():
                tcp_item = self.tcp_table[key]
                if len(tcp_item.t_buffer) != 0:
                    length = min(64, len(tcp_item.t_buffer))
                    tcp_packet = gen_tcp_packet(
                        tcp_item.d_addr,
                        0,
                        0,
                        tcp_item.socket.port,
                        payload=tcp_item.t_buffer[:length])
                    self.Transport_Network_queue.put_nowait(
                        TRAN_NET_ITEM(tcp_item.socket, tcp_item.d_addr,
                                      tcp_packet, 'TCP'))
                    tcp_item.t_buffer = tcp_item.t_buffer[length:]
                    self.tcp_table[key] = tcp_item


class R_PROCESS(Process):
    def __init__(self, tcp_table: dict[str, TCP_ITEM],
                 Network_Transport_queue: 'Queue[bytes]') -> None:
        self.Network_Transport_queue = Network_Transport_queue
        self.tcp_table = tcp_table
        super().__init__()

    def run(self):
        while True:
            if not self.Network_Transport_queue.empty():
                tcp_packet = self.Network_Transport_queue.get_nowait()
                tcp_port = get_tcp_d_port(tcp_packet)
                tcp_payload = get_tcp_payload(tcp_packet)
                tcp_item = self.tcp_table[str(tcp_port)]
                tcp_item.r_buffer = tcp_item.r_buffer + tcp_payload
                self.tcp_table[str(tcp_port)] = tcp_item


class TCP(Process):
    def __init__(self, barrier: Barrier_ = None) -> None:
        self.tcp_table: dict[str, TCP_ITEM] = Manager().dict()
        self.__event = Event()
        self.__barrier = Barrier(6, self.set_status)
        # self.Transport_Network_queue: Queue[bytes] = Queue()
        # self.Network_Transport_queue: Queue[bytes] = Queue()
        super().__init__()

    def set_status(self):
        self.__event.set()

    def run(self) -> None:
        Transport_Network_queue: Queue[TRAN_NET_ITEM] = Queue()
        Network_Transport_queue: Queue[bytes] = Queue()
        network = NETWORK(Transport_Network_queue, Network_Transport_queue,
                          self.__barrier)
        network.start()
        t_process = T_PROCESS(self.tcp_table, Transport_Network_queue)
        t_process.start()
        r_process = R_PROCESS(self.tcp_table, Network_Transport_queue)
        r_process.start()
        self.__barrier.wait()
        while True:
            pass

    def bind(self, _socket: SOCKET):
        port = _socket.port
        if str(port) in self.tcp_table:
            print('error: Address already in use')
        self.tcp_table[str(port)] = TCP_ITEM(_socket)

    def connect(self, d_addr: D_ADDR, _socket: SOCKET):
        #three way handshake
        port = _socket.port
        if str(port) in self.tcp_table.keys():
            self.tcp_table[str(port)].d_addr = d_addr
            self.tcp_table[str(port)].is_connected = True
        else:
            self.tcp_table[str(port)] = TCP_ITEM(_socket,
                                                 d_addr,
                                                 is_connected=True)

    def read(self,
             _socket: SOCKET,
             blocking: bool = None,
             buffer_size: int = None):
        port = _socket.port
        tcp_item = self.tcp_table[str(port)]
        print(tcp_item)
        if not tcp_item.is_closed:
            temp = tcp_item.r_buffer
            tcp_item.r_buffer = b''
            self.tcp_table[str(port)] = tcp_item
            return temp

        return -1

    def write(self, _socket: SOCKET, data: bytes):
        port = _socket.port
        tcp_item = self.tcp_table[str(port)]
        if tcp_item.is_connected:
            tcp_item.t_buffer = tcp_item.t_buffer + data
            self.tcp_table[str(port)] = tcp_item
            return 1

        return -1

    def get_status(self):
        if self.__event.is_set():
            return 1
        return 0


if __name__ == '__main__':
    import time
    tcp = TCP()
    tcp.start()
    time.sleep(3)
    _socket = SOCKET('192.168.0.2', 10)
    d_addr = D_ADDR('192.168.0.1', 10)
    tcp.connect(d_addr, _socket)
    tcp.write(_socket, b'abc')
    tcp.join()