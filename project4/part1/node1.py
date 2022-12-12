from ftp_utils import check_input
import pyfiglet


class FTP:
    def __init__(self):
        result = pyfiglet.figlet_format(text="Athernet  FTP".upper(),
                                        font="slant")
        print(result)
        pass

    def start(self):
        self.command_input()
        pass

    def command_input(self) -> str:
        flag = False
        while not flag:
            command_str = input('Please input FTP command: ')
            flag = check_input(command_str)
        return command_str


if __name__ == '__main__':
    ftp = FTP()
    ftp.start()