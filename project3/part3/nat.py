import os
import socket
from multiprocessing import Queue, Process
from threading import Thread

from mac import MAC
from network_utils import get_IP_dest, send_routine, recv_routine, get_ICMP_payload, gen_IP_ICMP_datagram


class T_MODULE(Thread):
    def __init__(self, Transport_Network_queue: Queue,
                 Network_Link_queue: Queue, sock: socket.socket) -> None:
        self.Transport_Network_queue = Transport_Network_queue
        self.Network_Link_queue = Network_Link_queue
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            sending_ts, src_addr = recv_routine(self.sock)
            self.Network_Link_queue.put(
                gen_IP_ICMP_datagram(sending_ts, src_addr))


class R_MODULE(Thread):
    def __init__(self, Link_Network_queue: Queue, sock: socket.socket) -> None:
        self.Link_Network_queue = Link_Network_queue
        self.sock = sock
        super().__init__()

    def run(self):
        ident = os.getpid()
        magic = b'1234567890'
        while True:
            ip_datagram: list[int] = self.Link_Network_queue.get()
            send_routine(self.sock, get_IP_dest(ip_datagram), ident, magic,
                         get_ICMP_payload(ip_datagram))


class NETWORK(Process):
    def __init__(self, Transport_Network_queue: Queue,
                 Network_Transport_queue: Queue) -> None:
        self.Transport_Network_queue = Transport_Network_queue
        self.Network_Transport_queue = Network_Transport_queue
        super().__init__()

    def run(self):
        Network_Link_queue = Queue()
        Link_Network_queue = Queue()
        mac = MAC(Network_Link_queue, Link_Network_queue)
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                             socket.IPPROTO_ICMP)
        sock.bind(('', 10001))
        t_module = T_MODULE(self.Transport_Network_queue, Network_Link_queue,
                            sock)
        t_module.start()
        r_module = R_MODULE(Link_Network_queue, sock)
        r_module.start()
        mac.start()
        mac.join()


def main():
    Transport_Network_queue = Queue()
    Network_Transport_queue = Queue()
    net = NETWORK(Transport_Network_queue, Network_Transport_queue)
    net.start()
    net.join()


if __name__ == '__main__':
    main()