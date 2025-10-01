import bencodepy

# Was creating double calls in specific scenarios. Might try again to implement my own version but now will just call in the modules themselves.

# def encode(data:bytes) -> dict:
#     return bencodepy.encode(data)

# def decode(data: bytes) -> dict:
#     assert isinstance(data, (bytes, bytearray)), "Input must be bencoded bytes"
#     return bencodepy.decode(data)