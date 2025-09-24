import asyncio
import logging
import struct
from asyncio import Queue
from concurrent.futures import CancelledError

import bitstring

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
            except ProtocolError as e:
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

