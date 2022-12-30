import time
from mac import MAC
from multiprocessing import Queue, Process, Barrier
from multiprocessing.synchronize import Barrier as Barrier_
from threading import Thread
from nat_utils import gen_Anet_IP_datagram, gen_tcp_packet, get_tcp_payload_from_IP, split_ftp_data
from dataclasses import dataclass
from tcp_utils import SOCKET, D_ADDR
import ftplib
import jellyfish


class T_MODULE(Process):
    def __init__(self, Network_Link_queue: 'Queue[bytes]') -> None:
        self.Network_Link_queue = Network_Link_queue
        super().__init__()

    def run(self):
        while True:
            pass
            # ip_datagram = gen_Anet_IP_datagram(t_item.data, t_item.socket)
            # self.Network_Link_queue.put(ip_datagram)


class R_MODULE(Process):
    def __init__(self, Link_Network_queue: 'Queue[bytes]',
                 Network_Link_queue: 'Queue[bytes]') -> None:
        self.Link_Network_queue = Link_Network_queue
        self.Network_Link_queue = Network_Link_queue
        super().__init__()

    def run(self):
        self.ftp = FtpClient()
        while True:
            # get an ip datagram, send command to ftp server
            ip_datagram: bytes = self.Link_Network_queue.get()
            # Firstly,here, we get athernet ip datagram and change it to standard ip datagram
            # Sencondly, use ftplib to send ftp commend and waiting response
            # Finally generate a Athnet IP datagram by calling gen_Anet_IP_datagram and put it into
            # self.Network_Link_queue
            command: str = get_tcp_payload_from_IP(ip_datagram)
            cmd, res = self.ftp.send_ftp_command(command[:-2])  # due to \r\n
            # print(f'cmd {cmd}')
            # print(f'res {res}')
            dataset: list = split_ftp_data(res)
            port = 10001 if cmd in ['list', 'retr'] else 10000
            # pack data and send to node1
            for i, data in enumerate(dataset):
                fin = int(i == len(dataset) - 1)
                print(f'ftp server response: {data}')
                if fin:
                    data += '\r\n'
                tcp = gen_tcp_packet(D_ADDR('192.168.1.2', port),
                                     i,
                                     fin,
                                     21,
                                     ack_num=1,
                                     payload=data.encode('utf-8'))
                ip_datagram = gen_Anet_IP_datagram('140.110.96.68',
                                                   '192.168.1.2', 'TCP', tcp)
                self.Network_Link_queue.put(ip_datagram)


class NETWORK(Process):
    def __init__(self, barrier: Barrier_ = None) -> None:
        self.barrier = barrier if barrier != None else Barrier(5)
        super().__init__()

    def run(self):
        Network_Link_queue = Queue()
        Link_Network_queue = Queue()
        mac = MAC(Network_Link_queue, Link_Network_queue, self.barrier)
        t_module = T_MODULE(Network_Link_queue)
        t_module.start()
        r_module = R_MODULE(Link_Network_queue, Network_Link_queue)
        r_module.start()
        mac.start()
        mac.join()


class FtpClient:
    RETR_BLOCK_SIZE = 4096
    OPERATIONS = [
        'user', 'pass', 'pwd', 'cwd', 'pasv', 'list', 'retr', 'connect', 'quit'
    ]

    def __init__(self):
        self.ftp = ftplib.FTP()

    def user_cmd(self, *args):
        assert args
        return self.ftp.sendcmd(f'USER {args[0]}')

    def pass_cmd(self, *args):
        assert args
        return self.ftp.sendcmd(f'PASS {args[0]}')

    def connect_cmd(self, *args):
        host = (args or ["ftp.ncnu.edu.tw"])[0]
        print(f'connecting to host: {host}')
        return self.ftp.connect(host)

    def pwd_cmd(self, *args):
        return self.ftp.sendcmd('PWD')

    def cwd_cmd(self, *args):
        assert args
        return self.ftp.cwd(args[0])

    def pasv_cmd(self, *args):
        assert args
        pasv = self._fuzzy_get_operation_name(args[0], ops=['true', 'false'])
        if 'false' == pasv:
            return self.ftp.sendcmd('PASV False')
        else:
            return self.ftp.sendcmd('PASV True')

    def list_cmd(self, *args):
        files = []
        self.ftp.dir(files.append)
        return '\n'.join(files)

    def retr_cmd(self, *args):
        assert args
        file = []
        self.ftp.retrbinary(f'RETR {args[0]}',
                            file.append,
                            blocksize=FtpClient.RETR_BLOCK_SIZE)
        return (b''.join(file)).decode('utf-8')

    def quit_cmd(self, *args):
        return self.ftp.quit()

    def error(self, *args):
        return 'Wrong CMD!'

    def _fuzzy_get_operation_name(self, operation: str, ops=None) -> str:
        if ops is None:
            ops = self.OPERATIONS
        op = operation.lower()
        operation = sorted(
            ops, key=lambda x: jellyfish.levenshtein_distance(x, op))[0]
        if jellyfish.levenshtein_distance(operation, op) >= 3:
            raise ValueError(f'Invalid operation: {operation}')
        return operation

    def send_ftp_command(self, cmd_line: str):
        cmd_line = cmd_line.strip().split()
        try:
            cmd = self._fuzzy_get_operation_name(cmd_line[0])
            res = getattr(self, cmd + '_cmd', 'error')(*cmd_line[1:])
            return cmd, res
        except Exception as error:
            return cmd_line, error.args[0]


if __name__ == '__main__':
    nat = NETWORK()
    nat.start()
    nat.join()