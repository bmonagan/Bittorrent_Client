import bencodepy

def encode(data):
    return bencodepy.encode(data)

def decode(data):
    return bencodepy.decode(data)