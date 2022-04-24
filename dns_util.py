import socket

__all__ = [
    'activate',
    'deactivate',
    'register',
    'get_dns_records',
    'clear_dns',
]

from typing import Union, Tuple, List

bak_getaddrinfo = socket.getaddrinfo
dns_records = {
    'lncn.org': '104.16.58.66'
}


def new_getaddrinfo(*args, **kwargs):
    if args[0] in dns_records:
        args = (dns_records[args[0]],) + args[1:]
    return bak_getaddrinfo(*args, **kwargs)


def activate():
    socket.getaddrinfo = new_getaddrinfo


def deactivate():
    socket.getaddrinfo = bak_getaddrinfo


def register(records: Union[List[Tuple[str, str]], Tuple[str, str]]):
    if isinstance(records, Tuple):
        records = [records]
    for ns, host in records:
        dns_records[ns] = host


def get_dns_records():
    return dns_records


def clear_dns():
    dns_records.clear()
