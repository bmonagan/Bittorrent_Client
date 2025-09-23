
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
