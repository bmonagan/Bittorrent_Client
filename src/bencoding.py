import bencodepy
# Would be interesting to do code these manually in the future.
# There are a few different libraries but it would make sense to have something of my own for it.

def encode(data):
    return bencodepy.encode(data)

def decode(data):
    return bencodepy.decode(data)