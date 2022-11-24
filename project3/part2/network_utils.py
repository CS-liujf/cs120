'''
https://blog.csdn.net/weixin_42000303/article/details/122182539
'''


def ip2int(ip: str) -> int:
    return sum(int(v) * 256**(3 - i) for i, v in enumerate(ip.split(".")))


def int2ip(number: int) -> str:
    result = []
    for i in range(4):
        number, mod = divmod(number, 256)
        result.insert(0, mod)
    return ".".join(str(i) for i in result)


def dec_to_bin_list(number: int, length: int) -> list[int]:
    return [int(x) for x in f'{{0:0{length}b}}'.format(number)]


def bin_list_to_dec(bin_list: list[int]) -> int:
    return int(''.join(map(str, bin_list)), 2)


def gen_IP_datagram(payload: list[int]):
    s_ip_int = ip2int('192.168.1.2')
    d_ip_int = ip2int('10.20.196.226')
    s_addr_list = dec_to_bin_list(s_ip_int, 32)
    d_addr_list = dec_to_bin_list(d_ip_int, 32)
    tot_len = len(payload)
    return s_addr_list + d_addr_list + payload


if __name__ == '__main__':
    gen_IP_datagram([])