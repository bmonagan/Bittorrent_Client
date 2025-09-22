import random

def generate_peer_id()-> str:
    """
    Generates a unique BitTorrent peer ID using the Azureus-style convention.

    The peer ID consists of a fixed prefix '-BK0001-' followed by a 12-character
    random alphanumeric suffix. This format helps identify the client and version.

    Must be exactly 20 bytes. String representations of numbers are 1 byte each.

    Returns:
        str: A 20-character string representing the BitTorrent peer ID.
    """
    prefix = '-BK0001-'
    length = 12
    random_choices = random.choices('0123456789', k=length)
    suffix = ''.join(random_choices)
    return prefix + suffix