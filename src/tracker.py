
import aiohttp
import random
import logging
import socket
from struct import unpack
from urllib.parse import urlencode

from . import bencoding


class TrackerResponse:
    pass
class Tracker:

    def __init__(self,torrent):
        self.torrent = torrent
        self.peer_id = generate_peer_id()
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
        pass
    
    def raise_for_error(self,tracker_response):
        pass
    
    def _construct_tracker_parameters(self):
        pass
    
    def _decode_port(port):
        pass
    import random

    def generate_peer_id()-> str:
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
