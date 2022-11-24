from mac_layer import MAC
from multiprocessing import Queue, Pipe, Process, Barrier


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


def bits2a(b):
    return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(b)] * 8))


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


class NETWORK(Process):
    def __init__(self, Transport_Network_queue: Queue) -> None:
        self.Transport_Network_queue = Transport_Network_queue
        super().__init__()

    def run(self):
        Network_Link_queue = Queue()
        Link_Network_queue = Queue()
        mac = MAC(Network_Link_queue, Link_Network_queue)
        mac.start()
        while True:
            pass


def main():
    temp = [i + 58 for i in range(7)]
    res = []
    for i in range(48, 85):
        if i in temp:
            continue
        res.append(40 * chr(i) + '\n')
    # print(len(res))
    with open('INPUT.txt', 'w') as f:
        f.writelines(res)


if __name__ == '__main__':
    # main()
    read_data()