"""
This module provides classes for interacting with BitTorrent trackers.

- TrackerResponse: Parses and exposes information from a tracker's bencoded response, including peers, completion stats, and failure reasons.
- Tracker: Manages communication with a tracker for a given torrent, including announcing, peer discovery, and session management.

Designed for use in a BitTorrent client implementation.
"""
# Standard library imports
import logging
import random
import socket
from struct import unpack
from urllib.parse import urlencode

# Third-party imports
import aiohttp
from bencodepy import decode



class TrackerResponse:
    def __init__(self, repsonse: dict):
        self.response = repsonse
    
    @property
    def failure(self):
        # b'' means that it is a bytes literal, meaning it contains raw byte data.
        if b'failure reason' in self.response:
            return self.response[b'failure reason'].decode('utf-8')
        return None
    
    @property
    def interval(self) -> int:
        return self.response.get(b'interval',0)
    
    @property
    def complete(self) -> int:
        return self.response.get(b'complete',0)

    @property 
    def incomplete(self) -> int:
        """
        Number of leechers.
        """
        return self.response.get(b'incomplete',0)
    
    @property 
    def peers(self):
        """
        a list of tuples for each peer (ip,port)
        """
        if b'failure reason' in self.response:
            reason = self.response[b'failure reason'].decode('utf-8')
            raise RuntimeError(f"Tracker failure: {reason}")
        if b'peers' not in self.response:
            raise RuntimeError("No peers returned by tracker. The tracker may be overloaded, down, or your request was invalid.")
        peers = self.response[b'peers']
        if type(peers) == list:
            logging.debug('Dictionary model peers are return by tracker')
            raise NotImplementedError
        else:
            logging.debug('Binary model peers are returned by tracker')
            peers = [peers[i:i+6] for i in range(0, len(peers), 6)]
            return [(socket.inet_ntoa(p[:4]), self.decode_port(p[4:]))
                    for p in peers]
    
    def decode_port(self, port):
        return unpack(">H", port)[0]

    def __str__(self):
        return "incomplete: {incomplete}\n" \
               "complete: {complete}\n" \
               "interval: {interval}\n" \
               "peers: {peers}\n".format(
                   incomplete=self.incomplete,
                   complete=self.complete,
                   interval=self.interval,
                   peers=", ".join([x for (x, _) in self.peers]))


class Tracker:
    """
    Connection to a tracker for a given torrent that is either under download or seeding state.
    """

    def __init__(self, torrent):
        self.torrent = torrent
        self.peer_id = self.generate_peer_id()
        self.http_client = None  # Don't create session here

    async def connect(self,
                      first: bool = None,
                      uploaded: int = 0,
                      downloaded: int = 0):
        if self.http_client is None:
            self.http_client = aiohttp.ClientSession()
        params = { 
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.torrent.total_size - downloaded,
            'compact': 1
        }
        if first:
            params['event'] = 'started'
        url = self.torrent.announce + '?' + urlencode(params)
        logging.info('Connecting to tracker at: %s', url)

        async with self.http_client.get(url) as response:
            if not response.status == 200:
                raise ConnectionError('Unable to connect to tracker')
            data = await response.read()
            return TrackerResponse(decode(data))

    async def close(self):
        if self.http_client:
            await self.http_client.close()
    
    def raise_for_error(self, tracker_response):
        pass
    
    def _construct_tracker_parameters(self):
        #TODO update when communicating with tracker.
        return {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'port': 6889,
            'uploaded': 0,
            'downloaded': 0,
            'left': 0,
            'compact': 1
        }
    def generate_peer_id(self)-> str:
        """
        Generates a unique BitTorrent peer ID using the Azureus-style convention.
        Must be exactly 20 bytes. String representations of numbers are 1 byte each.
        Returns:
            str: A 20-character string representing the BitTorrent peer ID.
        """
        prefix = '-BK0001-'
        length = 12
        random_choices = random.choices('0123456789', k=length)
        suffix = ''.join(random_choices)
        return prefix + suffix
