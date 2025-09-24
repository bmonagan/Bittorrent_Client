import asyncio
import logging
import struct
from asyncio import Queue
from concurrent.futures import CancelledError

import bitstring

from . import bencoding

REQUEST_SIZE = 2**14

class ProtocolError(BaseException):
    # TODO: implemnt protocol error class.
    pass

class PeerConnection:
    def __init__(self,queue:Queue, info_hash,
                peer_id, piece_manager, on_block_cb = None ):
        self.my_state = []
        self.peer_state = []
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.remote_id = None
        self.writer = None
        self.reader = None
        self.piece_manager = piece_manager
        self.on_block_cb = on_block_cb
        self.future= asyncio.ensure_future(self.start())
    
    async def _start(self):
        while 'stopped' not in self.my_state:
            ip,port = await self.queue.get()
            logging.info('Got assigned peer with:{ip}'.format(ip=ip))

            try:
                #TODO's: Fix second loop not starting
                # Add support for sending data
                self.reader, self.writer = await asyncio.open_connection(
                    ip,port)
                logging.info('Connection open to peer: {ip}'.format(ip=ip))

                buffer = await self._handshake()
                # default state for a connection
                self.my_state.append('choked')

                # Lets the peer know of interest
                await self._send_interested()
                self.my_state.append('interested')

                #Start reading responses as a stream of messages as
                # long as the connection is open and data is transmitted 
                async for message in PeerStreamIterator(self.reader,buffer):
                    if 'stopped' in self.my_state:
                        break
                    if type(message) is BitField:
                        self.piece_manager.add_peer(self.remote_id,
                                                    message.bitfield)
                    elif type(message) is Interested:
                        self.peer_state.append('interested')
                    elif type(message) is NotInterested:
                        if 'interested' in self.peer_state:
                            self.peer_state.remove('interested')
                    elif type(message) is Choke:
                        self.my_state.append('choked')
                    elif type(message) is Unchoke:
                        if 'choked' in self.my_state:
                            self.my_state.remove('choked')
                    elif type(message) is Have:
                        self.piece_manager.update_peer(self.rmeote_id,
                                                       message.index)
                    elif type(message) is KeepAlive:
                        pass
                    elif type(message) is Piece:
                        self.my_state.remove('pending_request')
                        self.on_block_cb(
                            peer_id=self.remote_id,
                            piece_index=message.index,
                            block_offset=message.begin,
                            data=message.block)
                    elif type(message) is Request:
                        # TODO support for sending data
                        logging.info('Ignoring the received Request message.')
                    elif type(message) is Cancel:
                        # TODO support for sending data
                        logging.info('Ignoring the reeived Cancel Message.')
                    
                    # TODO maybe find a cleaner way to rewrite this section.
                    # it might be the best way to do it but pretty ugly.
                    if 'choked' not in self.my_state:
                        if 'interested' in self.my_state:
                            if 'pending_request' not in self.my_state:
                                self.my_state.append('pending_request')
                                await self._request_piece()
            except ProtocolError:
                logging.exception('Protocol error')
            except (ConnectionRefusedError, TimeoutError):
                logging.warning('Unable to connect to peer')
            except (ConnectionResetError, CancelledError):
                logging.warning('Connection closed')
            except Exception as e:
                logging.exception('An error occurred')
                self.cancel()
                raise e
            self.cancel()
    def cancel(self):
        """
        Sends cancel message to the remote peer and closes the connection
        """

        logging.info('Closing peer {id}'.format(id=self.remote_id))
        if not self.future.done():
            self.future.cancel()
        if self.writer:
            self.writer.close()

        self.queue.task_done()
    
    def stop(self):
        """
        Stops this connection from the current peer and stops 
        new connections
        """
        self.my_state.append('stopped')
        if not self.future.done():
            self.future.cancel()

    async def _request_piece(self):
        block = self.piece_manager.next_request(self.remote_id)
        if block:
            message = Request(block.piece, block.offset, block.length).encode()

            logging.debug('Requesting block {block} for piece {piece} '
                          'of {length} bytes from peer {peer}'.format(
                              piece=block.piece,
                              block=block.offset,
                              length=block.length,
                              peer=self.remote_id))
            
            self.writer.write(message)
            await self.writer.drain()
                        
    async def _handshake(self):
        """
        Sends the initial handshake to the remote peer and wait for
        the peer to respond with its handshake
        """
        self.writer.write(HandShake(self.info_hash,self.peer_id).encode())
        await self.writer.drait()

        buf = b""
        tries = 1 
        while len(buf) < Handshake.length and tries < 10:
            tries += 1 
            buf = await self.reader.read(PeerStreamIterator.CHUNK_SIZE)
        
        response = Handshake.decode(buf[:Handshake.length])
        if not response:
            raise ProtocolError('Unable to recieve and parse a handshake')
        if not response.info_hash == self.info_hash:
            raise ProtocolError('Handshake with invalid info_hash')
        
        #TODO: Validate that the peer_id received from the peer matches tracker
        self.remote_id = response.peer_id
        logging.info('Handshake with peer was successful')

        return buf[Handshake.length:]


class PeerStreamIterator:
    """
    The `PeerStreamIterator` is an async iterator that continuously reads from
    the given stream reader and tries to parse valid BitTorrent messages from
    off that stream of bytes.

    If the connection is dropped, something fails the iterator will abort by
    raising the `StopAsyncIteration` error ending the calling iteration.
    """
    CHUNK_SIZE = 10*1024

    def __init__(self, reader, initial:bytes = None):
        self.reader = reader
        self.buffer = initial if initial else b''

    async def __aiter__(self):
        return self
    
    async def __anext__(self):
        # Read data from the socket. When we have enough data to parse, parse
        # it and return the message. Until then keep reading from stream
        while True:
            try:
                data = await self.reader.read(PeerStreamIterator.CHUNK_SIZE)
                if data:
                    self.buffer += data
                    message = self.parse()
                    if message:
                        return message
                else:
                    logging.debug('No data read from stream')
                    if self.buffer:
                        message = self.parse()
                        if message:
                            return message 
                    raise StopAsyncIteration()
            except ConnectionResetError:
                logging.debug('Connection closed by peer')
                raise StopAsyncIteration()
            except CancelledError:
                raise StopAsyncIteration()
            except StopAsyncIteration as e:
                raise e 
            except Exception:
                logging.exception('Error when iterating over stream!')
        raise StopAsyncIteration()  



class PeerMessage:
    """
    A message between two peers.

    All of the remaining messages in the protocol take the form of:
        <length prefix><message ID><payload>

    - The length prefix is a four byte big-endian value.
    - The message ID is a single decimal byte.
    - The payload is message dependent.

    NOTE: The Handshake messageis different in layout compared to the other
          messages.

    Read more:
        https://wiki.theory.org/BitTorrentSpecification#Messages

    BitTorrent uses Big-Endian (Network Byte Order) for all messages, this is
    declared as the first character being '>' in all pack / unpack calls to the
    Python's `struct` module.
    """
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    BitField = 5
    Request = 6
    Piece = 7
    Cancel = 8
    Port = 9
    Handshake = None  # Handshake is not really part of the messages
    KeepAlive = None  # Keep-alive has no ID according to spec

    def encode(self) -> bytes:
        """
        Encodes this object instance to the raw bytes representing the entire
        message (ready to be transmitted).
        """
        pass

    @classmethod
    def decode(cls, data: bytes):
        """
        Decodes the given BitTorrent message into a instance for the
        implementing type.
        """
        pass

class Handshake(PeerMessage):
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

