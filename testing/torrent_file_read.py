from bencodepy import decode

def read_torrent_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
        return decode(data)
    return None

file_path = r"data\cachyos.torrent"

print(read_torrent_file(file_path))
