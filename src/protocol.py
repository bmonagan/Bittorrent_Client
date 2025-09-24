import asyncio
import logging
import struct
from asyncio import Queue
from concurrent.futures import CancelledError

import bitstring

REQUEST_SIZE = 2**14

class ProtocolError(BaseException):
    pass

class PeerConnection:
    pass

class PeerStreamIterator:
    pass

class PeerMessage:
    pass

class HandShake(PeerMessage):
    pass

class KeepAlive(PeerMessage):
    pass

class BitField(PeerMessage):
    pass

class Interested(PeerMessage):
    pass

class NotInterested(PeerMessage):
    pass

class Choke(PeerMessage):
    pass

class Unchoke(PeerMessage):
    pass

class Have(PeerMessage):
    pass

class Request(PeerMessage):
    pass

class Piece(PeerMessage):
    pass

class Cancel(PeerMessage):
    pass

