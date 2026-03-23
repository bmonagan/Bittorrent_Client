import hashlib
from collections import namedtuple
from typing import Any, cast
from bencodepy import decode

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
        info_hash (bytes): SHA-1 hash of the bencoded 'info' dictionary.
    """
    def __init__(self,filename):
        self.filename = filename
        self.files = []
        self.meta_info: dict[bytes, Any] = {}

        with open(self.filename,'rb') as f:
            meta_info = f.read()
            self.meta_info = cast(dict[bytes, Any], decode(meta_info))
            raw_info = self._extract_raw_info_dict(meta_info)
            # BitTorrent v1 info_hash is SHA-1 over the exact raw bencoded info dict bytes.
            self.info_hash = hashlib.sha1(raw_info).digest()
            self._identify_files()

    @staticmethod
    def _read_bencoded_value_end(data: bytes, start: int) -> int:
        token = data[start:start + 1]
        if token == b'i':
            return data.index(b'e', start) + 1
        if token == b'l':
            idx = start + 1
            while data[idx:idx + 1] != b'e':
                idx = Torrent._read_bencoded_value_end(data, idx)
            return idx + 1
        if token == b'd':
            idx = start + 1
            while data[idx:idx + 1] != b'e':
                key_end = data.index(b':', idx)
                key_length = int(data[idx:key_end])
                idx = key_end + 1 + key_length
                idx = Torrent._read_bencoded_value_end(data, idx)
            return idx + 1
        if b'0' <= token <= b'9':
            length_end = data.index(b':', start)
            length = int(data[start:length_end])
            return length_end + 1 + length
        raise ValueError('Invalid bencoded token while parsing info dictionary')

    @classmethod
    def _extract_raw_info_dict(cls, meta_info: bytes) -> bytes:
        if not meta_info.startswith(b'd'):
            raise ValueError('Invalid torrent file: top-level bencode is not a dictionary')

        idx = 1
        while meta_info[idx:idx + 1] != b'e':
            key_end = meta_info.index(b':', idx)
            key_length = int(meta_info[idx:key_end])
            key_start = key_end + 1
            key = meta_info[key_start:key_start + key_length]

            value_start = key_start + key_length
            value_end = cls._read_bencoded_value_end(meta_info, value_start)

            if key == b'info':
                return meta_info[value_start:value_end]

            idx = value_end

        raise ValueError('Invalid torrent file: missing info dictionary')

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
    def announce_urls(self) -> list[str]:
        """
        Returns announce URLs sorted by protocol preference.

        HTTP(S) trackers are listed first, then UDP trackers.
        """
        http_urls = []
        udp_urls = []

        def _bucket_url(raw_url):
            if not raw_url:
                return
            if isinstance(raw_url, bytes):
                url = raw_url.decode('utf-8', errors='ignore')
            else:
                url = str(raw_url)

            if url.startswith('http://') or url.startswith('https://'):
                http_urls.append(url)
            elif url.startswith('udp://'):
                udp_urls.append(url)

        announce_list = self.meta_info.get(b'announce-list', [])
        for tier in announce_list:
            if not tier:
                continue
            for raw_url in tier:
                _bucket_url(raw_url)

        _bucket_url(self.meta_info.get(b'announce'))
        urls = http_urls + udp_urls
        if urls:
            return urls
        raise RuntimeError("No valid announce URL found in torrent.")

    @property
    def announce(self) -> str:
        """
        Returns the preferred announce URL.
        """
        return self.announce_urls[0]

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
    def pieces(self) -> list[bytes]:
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
