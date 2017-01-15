from Crypto.Cipher import AES
from time import sleep
import binascii
import socket
import json
import os
import struct
import datetime

XIAOMI_PASSWORD = os.environ.get('XIAOMI_PASSWORD')

IV = bytearray([
    0x17, 0x99, 0x6d, 0x09, 0x3d, 0x28, 0xdd, 0xb3,
    0xba, 0x69, 0x5a, 0x2e, 0x6f, 0x58, 0x56, 0x2e
])


class XiaomiConnection(object):

    MULTICAST_PORT = 9898
    SERVER_PORT = 4321
    MULTICAST_ADDRESS = '224.0.0.50'
    SOCKET_BUFSIZE = 1024

    def __init__(self, **kwargs):
        self.multicast_address = kwargs.get(
            'multicast_address', self.MULTICAST_ADDRESS)
        self.multicast_port = kwargs.get(
            'multicast_port', self.MULTICAST_PORT)
        self.server_port = kwargs.get(
            'server_port', self.SERVER_PORT)
        self.socket = self._prepare_socket()

    def _prepare_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", self.multicast_port))
        mreq = struct.pack(
            "=4sl", socket.inet_aton(self.multicast_address),
            socket.INADDR_ANY
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.SOCKET_BUFSIZE)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return sock

    def send(self, data, ip=None, port=None):
        ip = ip or self.multicast_address
        port = port or self.multicast_port
        if type(data) is dict:
            data = json.dumps(data)
        return self.socket.sendto(
            data.encode("utf-8"), (ip, port)
        )

    def receive(self, **kwargs):
        while True:
            data, addr = self.socket.recvfrom(self.SOCKET_BUFSIZE)
            payload = json.loads(data.decode("utf-8"))
            # print payload
            conditions = [
                payload[key] == value
                for key, value in kwargs.items()
            ]
            if all(conditions):
                return payload

    def stream(self, **kwargs):
        while True:
            data, addr = self.socket.recvfrom(self.SOCKET_BUFSIZE)
            payload = json.loads(data.decode("utf-8"))
            # print payload
            conditions = [
                payload[key] == value
                for key, value in kwargs.items()
            ]
            if all(conditions):
                yield payload

    def whois(self):
        self.send({'cmd': 'whois'}, port=self.SERVER_PORT)
        return self.receive(cmd='iam')


class BaseXiaomiDevice(object):

    model = None

    def __init__(self, connection, gateway, sid, short_id, name=None):
        self.sid = sid
        self.short_id = short_id
        self.gateway = gateway
        self.connection = connection
        self.name = name

    def __repr__(self):
        return '{device}:{id}'.format(
            device=self.__class__.__name__,
            id=self.name or self.sid
        )

    def serialise(self):
        return {
            'sid': self.sid,
            'short_id': self.short_id,
            'model': self.model,
            'name': self.name
        }

    def read(self):
        self.connection.send(
            {'cmd': 'read', 'sid': self.sid},
            ip=self.gateway.ip
        )
        return self.connection.receive(cmd='read_ack', sid=self.sid)

    def listen(self, callback, **kwargs):
        for item in self.connection.stream(sid=self.sid):
            callback(item)

    @classmethod
    def deserialise(cls, connection, data):
        return cls(connection=connection, **data)

    def get_write_key(self, password, token):
        aes = AES.new(password, AES.MODE_CBC, str(IV))
        ciphertext = aes.encrypt(token)
        return binascii.hexlify(ciphertext).upper()

    def write(self, data):
        payload = {
            'cmd': 'write',
            'model': self.model,
            'sid': self.sid,
            'short_id': self.short_id,
            'data': {
                'key': self.get_write_key(
                    XIAOMI_PASSWORD, self.gateway.get_token()
                )
            }
        }
        payload['data'].update(data)
        self.connection.send(payload, ip=self.gateway.ip)
        return self.connection.receive(cmd='write_ack')

