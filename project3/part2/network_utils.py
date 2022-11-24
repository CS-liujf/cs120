'''
https://blog.csdn.net/weixin_42000303/article/details/122182539
'''

IP_HEADER_LEN = 32 + 32


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


def get_IP_payload(ip_datagram: list[int]):
    payload = ip_datagram[IP_HEADER_LEN:]
    payload = [payload[i:i + 8] for i in range(0, len(payload), 8)]
    res = ''.join(map(lambda x: chr(bin_list_to_dec(x)), payload))
    print(res)


if __name__ == '__main__':
    temp = [0 for _ in range(320 + 64)]
    temp = [0 for _ in range(64)] + 40 * dec_to_bin_list(74, 8)
    get_IP_payload(temp)
    # print(chr(48))
