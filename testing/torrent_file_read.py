from src.bencoding import decode

def read_torrent_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
        return decode(data)
    return None

file_path = r"data\historyofpelopon04thucuoft_archive.torrent"

torrent_data = read_torrent_file(file_path)
print(torrent_data) 