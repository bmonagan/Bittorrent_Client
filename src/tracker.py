
import aiohttp
import random
import logging
import socket
import random
from struct import unpack
from urllib.parse import urlencode

from . import bencoding


class TrackerResponse:
    def __init__(self,repsonse: dict):
        self.response = repsonse
    
    @property
    def failure(self):
        # b'' means that it is a bytes literal, meaning it contains raw byte data.
        if b'failure reason' in self.response:
            return self.response[b'failure reason'].decode('utf-8')
        return None
class Tracker:

    def __init__(self,torrent):
        self.torrent = torrent
        self.peer_id = self.generate_peer_id()
        self.http_client = aiohttp.ClientSeesion()

    async def connect(self,
                    first: bool=None,
                    uploaded: int=0,
                    downloaded: int=0):
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
        logging.info('Connecting to tracker at: ') + url

        async with self.http_client.get(url) as response:
            if not response.status == 200:
                raise ConnectionError('Unable to connect to tracker')
            data = await response.read()
            return TrackerResponse(bencoding.decode(data))
    def close(self):
        self.http_client.close()
    
    def raise_for_error(self,tracker_response):
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
    
    def _decode_port(port):
        return unpack(">H", port)[0]
    

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
