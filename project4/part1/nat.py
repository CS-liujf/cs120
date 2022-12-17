import time
from mac import MAC
from multiprocessing import Queue, Process, Barrier
from multiprocessing.synchronize import Barrier as Barrier_
from threading import Thread
from nat_utils import gen_Anet_IP_datagram
from dataclasses import dataclass
from tcp_utils import SOCKET, D_ADDR


@dataclass(frozen=True)
class TRAN_NET_ITEM:
    socket: SOCKET
    d_addr: D_ADDR
    payload: bytes
    protocol: str


class T_MODULE(Thread):
    def __init__(self, Network_Link_queue: 'Queue[bytes]') -> None:
        self.Network_Link_queue = Network_Link_queue
        super().__init__()

    def run(self):
        while True:
            pass
            # ip_datagram = gen_Anet_IP_datagram(t_item.data, t_item.socket)
            # self.Network_Link_queue.put(ip_datagram)


class R_MODULE(Thread):
    def __init__(self, Link_Network_queue: 'Queue[bytes]',
                 Network_Link_queue: 'Queue[bytes]') -> None:
        self.Link_Network_queue = Link_Network_queue
        self.Network_Link_queue = Network_Link_queue
        super().__init__()

    def run(self):
        while True:
            # get an ip datagram
            ip_datagram: bytes = self.Link_Network_queue.get()
            # Firstly,here, we get athernet ip datagram and change it to standard ip datagram
            # Sencondly, use ftplib to send ftp commend and waiting response
            # Finally generate a Athnet IP datagram by calling gen_Anet_IP_datagram and put it into
            # self.Network_Link_queue


class NETWORK(Process):
    def __init__(self,
                 Transport_Network_queue: 'Queue[TRAN_NET_ITEM]',
                 Network_Transport_queue: 'Queue[bytes]',
                 barrier: Barrier_ = None) -> None:
        self.barrier = barrier if barrier != None else Barrier(5)
        self.Transport_Network_queue = Transport_Network_queue
        self.Network_Transport_queue = Network_Transport_queue
        super().__init__()

    def run(self):
        Network_Link_queue = Queue()
        Link_Network_queue = Queue()
        mac = MAC(Network_Link_queue, Link_Network_queue, self.barrier)
        t_module = T_MODULE(self.Transport_Network_queue, Network_Link_queue)
        t_module.start()
        r_module = R_MODULE(Link_Network_queue, Network_Link_queue)
        r_module.start()
        mac.start()
        mac.join()