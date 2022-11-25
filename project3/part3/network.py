import time
from mac import MAC
from multiprocessing import Queue, Process
from multiprocessing.synchronize import Barrier as Barrier_
from threading import Thread
from network_utils import gen_IP_datagram, get_IP_payload, get_IP_source, bin2float, get_ICMP_payload


class T_MODULE(Thread):
    def __init__(self, Transport_Network_queue: Queue,
                 Network_Link_queue: Queue) -> None:
        self.Transport_Network_queue = Transport_Network_queue
        self.Network_Link_queue = Network_Link_queue
        super().__init__()

    def run(self):
        while True:
            payload: list[int] = self.Transport_Network_queue.get()
            ip_datagram = gen_IP_datagram(payload)
            self.Network_Link_queue.put(ip_datagram)


class R_MODULE(Thread):
    def __init__(self, Link_Network_queue: Queue) -> None:
        self.Link_Network_queue = Link_Network_queue
        super().__init__()

    def run(self):
        while True:
            # get an ip datagram
            ip_datagram: list[int] = self.Link_Network_queue.get()
            t = time.time()
            s_ip = get_IP_source(ip_datagram)
            ip_payload = get_IP_payload(ip_datagram)
            icmp_payload: str = ''.join(get_ICMP_payload(ip_payload))
            payload = bin2float(icmp_payload)
            print({'IP': s_ip, 'payload': payload, 'latency': t - payload})


class NETWORK(Process):
    def __init__(self, Transport_Network_queue: Queue,
                 Network_Transport_queue: Queue, barrier: Barrier_) -> None:
        self.barrier = barrier
        self.Transport_Network_queue = Transport_Network_queue
        self.Network_Transport_queue = Network_Transport_queue
        super().__init__()

    def run(self):
        Network_Link_queue = Queue()
        Link_Network_queue = Queue()
        mac = MAC(Network_Link_queue, Link_Network_queue, self.barrier)
        t_module = T_MODULE(self.Transport_Network_queue, Network_Link_queue)
        t_module.start()
        r_module = R_MODULE(Link_Network_queue)
        r_module.start()
        mac.start()
        mac.join()