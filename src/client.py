import asyncio
import logging
import math
import os
import time

from asyncio import Queue
from collections import namedtuple, defaultdict
from hashlib import sha1

from protocol import PeerConnection,REQUEST_SIZE
from tracker import Tracker

# Number of max peer connections per TorrentClient
MAX_PEER_CONNECTIONS = 40

class TorrentClient:
    """
    The torrent client is the local peer that holds peer-to-peer
    connections to download and upload pieces for a given torrent.

    Once started, the client makes periodic announce calls to the tracker
    registered in the torrent meta-data. These calls results in a list of
    peers that should be tried in order to exchange pieces.

    Each received peer is kept in a queue that a pool of PeerConnection
    objects consume. There is a fix number of PeerConnections that can have
    a connection open to a peer. Since we are not creating expensive threads
    (or worse yet processes) we can create them all at once and they will
    be waiting until there is a peer to consume in the queue.
    """

    def __init__(self, torrent):
        self.tracker = Tracker(torrent)
        # List of potential peers is the work queue
        self.available_peers = Queue()
        # The list of peers is the list of workers that *might* be connected
        # to a peer. Else they are waiting to consume new remote peers from
        # the `available_peers` queue. These are our workers!
        self.peers = []
        # The piece manager implements the strategy on which pieces to
        # request, as well as the logic to persist received pieces to disk.
        self.piece_manager = PieceManager(torrent)
        self.abort = False

    async def start(self):
        """
        Start downloading the torrent held by this client.

        This results in connecting to the tracker to retrieve the list of
        peers to communicate with. Once the torrent is fully downloaded or
        if the download is aborted this method will complete.
        """
        self.peers = [PeerConnection(self.available_peers,
                                     self.tracker.torrent.info_hash,
                                     self.tracker.peer_id,
                                     self.piece_manager,
                                     self._on_block_retrieved)
                                for _ in range(MAX_PEER_CONNECTIONS)] # TODO: figure out what this line is doing
        # Last announce call timestamp
        previous = None 
        # Default interval between announce calls
        interval = 30*60

        while True:
            if self.piece_manager.complete:
                logging.info('Torrent fully downloaded!')
                break
            if self.abort:
                logging.info('Aborting download...')
                break

            current = time.time()
            if (not previous) or (previous + interval < current):
                response = await self.tracker.connect(
                    first=previous if previous else False,
                    uploaded=self.piece_manager.bytes_uploaded,
                    downloaded=self.piece_manager.bytes_downloaded)
                
                if response:
                    previous = current
                    interval = response.interval
                    self._empty_queue()
                    for peer in response.peers:
                        self.available_peers.put_nowait(peer)

            else:
                await asyncio.sleep(5)
        self.stop()
    def _empty_queue(self):
        while not self.available_peers.empty():
            self.available_peers.get_nowait()

    def stop(self):
        """
        Stop the download or seeding process.
        """             
        self.abort = True
        for peer in self.peers:
            peer.stop()
        self.piece_manager.close()
        self.tracker.close()

    def _on_block_retrieved(self, peer_id, piece_index, block_offset, data):
        """
        Callback function called by the `PeerConnection` when a block is
        retrieved from a peer.

        :param peer_id: The id of the peer the block was retrieved from
        :param piece_index: The piece index this block is a part of
        :param block_offset: The block offset within its piece
        :param data: The binary data retrieved
        """
        self.piece_manager.block_received(
            peer_id=peer_id, piece_index= piece_index,
            block_offset=block_offset, data=data)

class Block:
    """
    The block is a partial piece, this is what is requested and transferred
    between peers.

    A block is most often of the same size as the REQUEST_SIZE, except for the
    final block which might (most likely) is smaller than REQUEST_SIZE.
    """
    Missing = 0
    Pending = 1
    Retrieved = 2

    def __init__(self, piece: int, offset: int, length: int):
        self.piece = piece
        self.offset = offset
        self.length = length
        self.status = Block.Missing
        self.data = None

class Piece:
    """
    The piece is a part of of the torrents content. Each piece except the final
    piece for a torrent has the same length (the final piece might be shorter).

    A piece is what is defined in the torrent meta-data. However, when sharing
    data between peers a smaller unit is used - this smaller piece is refereed
    to as `Block` by the unofficial specification (the official specification
    uses piece for this one as well, which is slightly confusing).
    """

    def __init__(self, index: int, block: [], hash_value):
        self.index = index
        self.blocks = blocks
        self.hash = hash_value
    
    def reset(self):
        """
        Reset all blocks to missing regarless of current state
        """
        for block in self.blocks:
            block.status = Block.Missing
    
    def next_request(self) -> Block:
        """
        Get the next Block to be requested
        """
        missing = [b for b in self.blocks if b.status is Block.Missing]
        if missing:
            missing[0].status = Block.Pending
            return missing[0]
        return None
    
    def block_received(self, offset: int, data: bytes):
        """
        Update block information that the given block is now received

        :param offset: The block offset (within the piece)
        :param data: The block data
        """
        matches = [b for b in self.blocks if b.offset == offset]
        block = matches[0] if matches else None
        if block:
            block.status = Block.Retrieved
            block.data = data
        else:
            logging.warning('Trying to complete a non-existing block {offset}'
                            .format(offset=offset))
    
    def is_complete(self) -> bool:
        """
        Checks if all blocks for this piece is retrieved (regardless of SHA1)

        :return: True or False
        """
        blocks = [b for b in self.blocks if b.status is not Block.Retrieved]
        return len(blocks) is 0
    
    def is_hash_matching(self):
        """
        Check if a SHA1 hash for all the received blocks match the piece hash
        from the torrent meta-info.

        :return: True or False
        """
        piece_hash = sha1(self.data).digest()
        return self.hash == piece_hash
    
    @property
    def data(self):
        """
        Return the data for this piece (by concatenating all blocks in order)

        NOTE: This method does not control that all blocks are valid or even
        existing!
        """
        retrieved = sorted(self.blocks, key=lambda b: b.offset)
        blocks_data = [b.data for b in retrieved]
        return b''.join(blocks_data)
    





    

        
