from bencodepy.decoder import decode
with open("data/historyofpelo.torrent", "rb") as f:
    data = f.read()
    print(data[820:830])

## b'contents.1'. Meaning that there is some problem with the way 
# it was encoded to begin with, or possible theres some 
# deeper error somewhere in my code or the bencdeopy library
