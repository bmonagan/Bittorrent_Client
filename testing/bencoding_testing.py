# pylint: skip-file
import bencodepy

# Example bencoded data (dictionary, string, list)

# All test data must be bytes and valid bencode
blabla = b'd3:cow3:moo4:spam4:eggse'  # dict: {b'cow': b'moo', b'spam': b'eggs'}
me = b'12:Middle Earth'  # string: b'Middle Earth'
list_example = b'l4:spam4:eggsi123ee'  # list: [b'spam', b'eggs', 123]

# Use bencodepy's decode (returns Python objects)


try:
	x = bencodepy.decode(blabla)
except ValueError as e:
	x = f"Error decoding blabla: {e}"


try:
	x2 = bencodepy.decode(me)
except ValueError as e:
	x2 = f"Error decoding me: {e}"


try:
	x3 = bencodepy.decode(list_example)
except ValueError as e:
	x3 = f"Error decoding list_example: {e}"

print(x)
print(x2)
print(x3)