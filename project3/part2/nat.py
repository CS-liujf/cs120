import socket
from multiprocessing import Queue, Process
from threading import Thread

from mac import MAC
from network_utils import gen_IP_port, bytes_to_01_list, gen_IP_datagram, SOCKET, get_IP_dest, get_IP_port, get_IP_data


class T_MODULE(Thread):
    def __init__(self, Transport_Network_queue: Queue,
                 Network_Link_queue: Queue, udp_socket) -> None:
        self.Transport_Network_queue = Transport_Network_queue
        self.Network_Link_queue = Network_Link_queue
        self.udp_socket = udp_socket
        super().__init__()

    def run(self):
        while True:
            data, s_addr = self.udp_socket.recvfrom(100)
            payload = gen_IP_port(s_addr[1]) + bytes_to_01_list(data)
            self.Network_Link_queue.put(gen_IP_datagram(payload, SOCKET(*s_addr)))


class R_MODULE(Thread):
    def __init__(self, Link_Network_queue: Queue, udp_socket) -> None:
        self.Link_Network_queue = Link_Network_queue
        self.udp_socket = udp_socket
        super().__init__()

    def run(self):
        while True:
            # get an ip datagram
            ip_datagram: list[int] = self.Link_Network_queue.get()
            addr = get_IP_dest(ip_datagram), get_IP_port(ip_datagram)
            self.udp_socket.sendto(get_IP_data(ip_datagram).encode('utf-8'), addr)


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
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        t_module = T_MODULE(self.Transport_Network_queue, Network_Link_queue, udp_socket)
        t_module.start()
        r_module = R_MODULE(Link_Network_queue, udp_socket)
        r_module.start()
        mac.start()
        mac.join()
        udp_socket.close()


def main():
    Transport_Network_queue = Queue()
    Network_Transport_queue = Queue()
    net = NETWORK(Transport_Network_queue, Network_Transport_queue)
    net.start()
    net.join()


if __name__ == '__main__':
    main()