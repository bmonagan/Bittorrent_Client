def encode(data):
    """
    Encodes data into bencode format.
    """
    if isinstance(data, int):  # Encode integers
        return f"i{data}e".encode()
    elif isinstance(data, bytes):  # Encode byte strings
        return f"{len(data)}:".encode() + data
    elif isinstance(data, str):  # Encode strings (convert to bytes)
        return f"{len(data)}:".encode() + data.encode()
    elif isinstance(data, list):  # Encode lists
        return b"l" + b"".join(encode(item) for item in data) + b"e"
    elif isinstance(data, dict):  # Encode dictionaries
        # Keys must be sorted and strings
        return (
            b"d"
            + b"".join(
                encode(str(key)) + encode(value) for key, value in sorted(data.items())
            )
            + b"e"
        )
    else:
        raise TypeError("Unsupported data type for bencoding")


def decode(data):
    """
    Decodes bencoded data.
    """
    def decode_item(index):
        if data[index] == ord("i"):  # Decode integer
            end = data.index(b"e", index)
            return int(data[index + 1 : end]), end + 1
        elif data[index] == ord("l"):  # Decode list
            index += 1
            lst = []
            while data[index] != ord("e"):
                item, index = decode_item(index)
                lst.append(item)
            return lst, index + 1
        elif data[index] == ord("d"):  # Decode dictionary
            index += 1
            dct = {}
            while data[index] != ord("e"):
                key, index = decode_item(index)
                value, index = decode_item(index)
                dct[key] = value
            return dct, index + 1
        elif data[index].isdigit():  # Decode string
            colon = data.index(b":", index)
            length = int(data[index:colon])
            start = colon + 1
            end = start + length
            return data[start:end], end
        else:
            raise ValueError("Invalid bencoded data")

    result, _ = decode_item(0)
    return result


# Example Usage
if __name__ == "__main__":
    # Example data
    data = {"key": "value", "list": [1, 2, 3], "nested": {"a": "b"}}

    # Encode
    encoded = encode(data)
    print("Encoded:", encoded)

    # Decode
    decoded = decode(encoded)
    print("Decoded:", decoded)
