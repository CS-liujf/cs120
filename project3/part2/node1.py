from network import NETWORK
from multiprocessing import Queue
from network_utils import SOCKET, TRANSPORT_ITEM, dec_to_bin_list


def gen_data():
    temp = [i + 58 for i in range(7)]
    res = []
    for i in range(48, 85):
        if i in temp:
            continue
        res.append(40 * chr(i) + '\n')
    # print(len(res))
    with open('INPUT.txt', 'w') as f:
        f.writelines(res)


def read_data():
    with open('INPUT.txt', 'r') as f:
        data = f.readlines()

    PAYLOAD_LEN = 320
    data = [i.rstrip() for i in data]  # remove \n
    bit_stream = ''
    for line in data:
        bit_stream += ''.join(
            ['{0:08b}'.format(ord(x)) for _, x in enumerate(line)])

    temp = [int(bit) for bit in bit_stream]
    return [temp[i:i + PAYLOAD_LEN] for i in range(0, len(temp), PAYLOAD_LEN)]
    # print(len(res))


def gen_UDP_datagram(payload: list[int], _socket: SOCKET):
    port_list = dec_to_bin_list(_socket.port, 16)
    return port_list + payload


def main():
    r_addr = SOCKET('127.0.0.1', 0)
    Transport_Network_queue: Queue[TRANSPORT_ITEM] = Queue()
    Network_Transport_queue = Queue()
    net = NETWORK(Transport_Network_queue, Network_Transport_queue)
    net.start()
    data_list = read_data()
    for data in data_list:
        data = gen_UDP_datagram(data, r_addr)
        Transport_Network_queue.put(TRANSPORT_ITEM(data, r_addr))

    net.join()
    # while True:
    # pass


if __name__ == '__main__':
    main()
    # read_data()