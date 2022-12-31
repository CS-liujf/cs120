from ftp_utils import check_addr_input, check_cmd_input
from tcp import TCP
from tcp_utils import SOCKET, D_ADDR
import pyfiglet
import time
from tqdm import tqdm

CRLF = '\r\n'


class FTP:
    def __init__(self, d_addr=None, tcp: TCP = None):
        result = pyfiglet.figlet_format(text="Athernet  FTP".upper(),
                                        font="slant")
        print(result)
        self.CMD_TABLE = {
            'USER': self.user_func,
            'PASS': self.pass_func,
            'PWD': self.pwd_func,
            'CWD': self.cwd_func,
            'PASV': self.pasv_func,
            'LIST': self.list_func,
            'RETR': self.retr_func
        }
        self.tcp = tcp if tcp != None else TCP()
        self.command_socket = SOCKET('192.168.1.2', 10000)
        self.data_socket = None
        self.tcp.start()

        self.server_cmd_addr = None
        self.server_data_addr = None

    def connect(self):
        while self.tcp.get_status() != 1:
            pass
        while not check_addr_input(
                server_addr := input('Server IP address: ')):
            pass
        server_addr = '140.110.96.68'  # just for test, remove for submitting
        self.server_cmd_addr = D_ADDR(server_addr, 21)
        self.tcp.connect(self.server_cmd_addr, self.command_socket)
        cmd_str = 'connect'.upper() + ' ' + server_addr + CRLF
        self.tcp.write(self.command_socket, cmd_str.encode('utf-8'))
        self.get_ftpcmd_status()
        # print(f'Connected to {server_addr}.')

    def user_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def pass_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def pwd_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def cwd_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def parse_port(self, res: str):
        # res = '227 Entering Passive Mode (140,110,96,68,205,75)'  #just for test, remember to remove!
        temp: tuple[int] = eval(res.split()[-1])
        port = temp[-2] * 256 + temp[-1]
        return port

    def pasv_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        res = self.get_ftpcmd_status()
        # get port
        port = self.parse_port(res)
        self.data_socket = SOCKET('192.168.1.2', self.command_socket.port + 1)
        self.server_data_addr = D_ADDR(self.server_cmd_addr.ip, port)

    def list_func(self, cmd_str: str):
        if self.data_socket == None:
            self.pasv_func('PASV'+CRLF)

        self.tcp.connect(self.server_data_addr, self.data_socket)
        self.send_ftpcmd(cmd_str)
        #self.get_ftpcmd_status()
        while True:
            res_buffer = self.tcp.read(self.data_socket)
            if res_buffer == -1:
                break
            elif res_buffer != b'':
                print(res_buffer.decode('utf-8'), end='')

        print('')
        self.data_socket = None
        self.server_data_addr = None

    def get_file_size(self, file_name: str):
        self.send_ftpcmd(f'SIZE {file_name}{CRLF}')
        flag = True
        while flag:
            res_buffer = self.tcp.read(self.command_socket)
            if res_buffer == -1 or res_buffer == b'':
                continue
            res_buffer = res_buffer.decode('utf-8')
            temp = res_buffer.split(CRLF)
            for msg in temp:
                try:
                    if msg[3] == ' ' and int(msg[:3]):
                        flag = False
                        break
                except:
                    continue
        return float(res_buffer.split()[-1])

    def retr_func(self, cmd_str: str):
        if self.data_socket == None:
            self.pasv_func('PASV'+CRLF)
        self.tcp.connect(self.server_data_addr, self.data_socket)
        # res = self.get_ftpcmd_status()
        file_name = cmd_str.split()[1]
        file_size = self.get_file_size(file_name)
        self.send_ftpcmd(cmd_str)
        with tqdm(desc=file_name,
                  total=file_size,
                  ncols=105,
                  unit='B',
                  bar_format='{l_bar}{bar}| [{elapsed}s, {rate_fmt}]') as bar:
            with open(f'./{file_name}', 'wb') as f:
                res = b''
                while True:
                    res_buffer = self.tcp.read(self.data_socket)
                    if res_buffer == -1:
                        break
                    elif res_buffer != b'':
                        res = res + res_buffer
                        bar.update(len(res_buffer))
                f.write(res)

        print('downloaded a file')
        self.data_socket = None
        self.server_data_addr = None

    def start(self):
        self.connect()
        while True:
            command_str = self.command_input()
            cmd = command_str.split()[0]
            self.CMD_TABLE[cmd](command_str)
            # self.send_ftpcmd(command_str)
            # self.get_ftpcmd_status()

    def command_input(self) -> str:
        while not check_cmd_input(
                command_str := input('Please input FTP command: ')):
            pass
        temp = command_str.split()
        temp[0] = temp[0].upper()
        return ' '.join(temp) + CRLF

    def send_ftpcmd(self, command_str: str):
        self.tcp.write(self.command_socket, command_str.encode('utf-8'))

    def get_ftpcmd_status(self) -> str:
        res = ''
        flag = True
        while flag:
            res_buffer = self.tcp.read(self.command_socket)
            if res_buffer == -1 or res_buffer == b'':
                continue
            res_buffer = res_buffer.decode('utf-8')
            print(res_buffer, end='')
            temp = res_buffer.split(CRLF)
            for msg in temp:
                try:
                    if msg[3] == ' ' and int(msg[:3]):
                        flag = False
                        break
                except:
                    continue

        print('')
        return res_buffer


if __name__ == '__main__':
    ftp = FTP()
    ftp.start()