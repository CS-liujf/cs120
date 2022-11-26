'''
https://stackoverflow.com/questions/16444726/binary-representation-of-float-in-python-bits-not-hex
'''
from network import NETWORK
from network_utils import binstr2list, float2bin
from multiprocessing import Queue, Barrier
import time
from network_utils import SOCKET, TRANSPORT_ITEM, dec_to_bin_list


def gen_icmp_datagram() -> list[int]:
    t = time.time()
    return binstr2list(float2bin(t))


def print_start():
    print('ping start!')


def main():
    r_addr = SOCKET('127.0.0.1', 0)
    Transport_Network_queue: Queue[TRANSPORT_ITEM] = Queue()
    Network_Transport_queue = Queue()
    barrier = Barrier(6, print_start)
    net = NETWORK(Transport_Network_queue, Network_Transport_queue, barrier)
    net.start()
    barrier.wait()  # wait for phy and mac
    for _ in range(10):
        data = gen_icmp_datagram()
        Transport_Network_queue.put(TRANSPORT_ITEM(data, r_addr))
        time.sleep(1)

    net.join()


if __name__ == '__main__':
    main()
    # read_data()