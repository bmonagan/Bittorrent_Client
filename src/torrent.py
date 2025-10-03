import hashlib
from collections import namedtuple
from bencodepy import encode,decode

#Reprsents the files within the torrent
TorrentFile = namedtuple('TorrentFile',['name','length'])

class Torrent:
    """
    Represents a .torrent file and provides access to its metadata.

    This class parses the .torrent file, extracts relevant information such as file name,
    file length, announce URL, piece hashes, and other metadata. It currently supports only
    single-file torrents. Multi-file torrents will raise a RuntimeError.

    Attributes:
        filename (str): Path to the .torrent file.
        files (list[TorrentFile]): List of files described by the torrent (single file supported).
        meta_info (dict): Decoded bencoded metadata from the torrent file.
        info_hash (bytes): SHA-256 hash of the bencoded 'info' dictionary.
    """
    def __init__(self,filename):
        self.filename = filename
        self.files = []

        with open(self.filename,'rb') as f:
            meta_info = f.read()
            self.meta_info = decode(meta_info)
            info = encode(self.meta_info[b'info'])
            self.info_hash = hashlib.sha256(info).digest()
            self._identify_files()

    def _identify_files(self):
        """
        identifies the files included in this torrent
        """

        if self.multi_file:
            #TODO further testing for multi-file torrents.
            root = self.meta_info[b'info'][b'name'].decode('utf-8')
            for file in self.meta_info[b'info'][b'files']:
                path = '/'.join([root] + [p.decode('utf-8') for p in file[b'path']])
                self.files.append(TorrentFile(path,file[b'length']))
        else:
            self.files.append(
                TorrentFile(
                    self.meta_info[b'info'][b'name'].decode('utf-8'),
                    self.meta_info[b'info'][b'length']))

    @property
    def announce(self) -> str:
        """
        Announces URL to tracker
        """
        print(self.meta_info.keys())
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
            return sum(f.length for f in self.files)
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
