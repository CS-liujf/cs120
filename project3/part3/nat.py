from mac import MAC
from multiprocessing import Queue, Pipe, Process, Barrier
from network_utils import get_IP_payload
from threading import Thread


class T_MODULE(Thread):
    def __init__(self, Transport_Network_queue: Queue,
                 Network_Link_queue: Queue) -> None:
        self.Transport_Network_queue = Transport_Network_queue
        self.Network_Link_queue = Network_Link_queue
        super().__init__()

    def run(self):
        pass


class R_MODULE(Thread):
    def __init__(self, Link_Network_queue: Queue) -> None:
        self.Link_Network_queue = Link_Network_queue
        super().__init__()

    def run(self):
        while True:
            # get an ip datagram
            ip_datagram: list[int] = self.Link_Network_queue.get()
            get_IP_payload(ip_datagram)


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
        t_module = T_MODULE(self.Transport_Network_queue, Network_Link_queue)
        t_module.start()
        r_module = R_MODULE(Link_Network_queue)
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