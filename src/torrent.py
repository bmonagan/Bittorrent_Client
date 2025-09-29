from hashlib import sha1
from collections import namedtuple

from .local_bencoding import encode, decode

#Reprsents the files within the torrent
TorrentFile = namedtuple('TorrentFile',['name','length'])

class Torrent:
    def __init__(self,filename):
        self.filename = filename
        self.files = []

        with open(self.filename,'rb') as f:
            meta_info = f.read()
            self.meta_info = decode(meta_info)
            info = encode(self.meta_info[b'info'])
            #TODO research if sha 1 is still the correct choice for something like this.
            self.info_hash = sha1(info).digest()
            self._identify_files()
        

    def _identify_files(self):
        """
        identifies the files included in this torrent
        """

        if self.multi_file:
            #TODO add support for multi-file torrents
            raise RuntimeError('Multi-file torrents is not supported!')
        self.files.append(
            TorrentFile(
                self.meta_info[b'info'][b'name'].decode('utf-8'),
                self.meta_info[b'info'][b'length']))
    
    @property
    def announce(self) -> str:
        """
        Announces URL to tracker
        """
        return self.meta_info[b'announce'].decode('utf-8')
    
    @property
    def multi_file(self) -> bool:
        """
        Checks if torrent contains multiple files
        """
        return b'files' in self.meta_info[b'info']
    
    @property
    def piece_length(self) -> int:
        """
        Gets the length in bytes for each piece of download
        """
        return self.meta_info[b'info'][b'piece length']
    
    @property
    def total_size(self) -> int:
        """
        :return: The total size (in bytes) for this torrent's data.
        """
        if self.multi_file:
            raise RuntimeError('Multi-file torrents are not supported!')
        return self.files[0].length
    
    @property
    def pieces(self) -> list[str]:
        """
        Breaks the string meta_info pieces into 20 byte long slices. 
        20 bytes being 20 characters in a string representation
        """
        data = self.meta_info[b'info'][b'pieces']
        pieces = []
        offset = 0
        length = len(data)

        while offset < length:
            pieces.append(data[offset:offset + 20])
            offset += 20
        return pieces 

    @property 
    def output_file(self):
        return self.meta_info[b'info'][b'name'].decode('utf-8')
    
    def __str__(self):
        return (f"Filename: {self.meta_info[b'info'][b'name'].decode('utf-8')}\n"
                f"File length: {self.meta_info[b'info'][b'length']}\n"
                f"Announce URL: {self.meta_info[b'announce'].decode('utf-8')}\n"
                f"Hash: {self.info_hash.hex()}")
