Fixes made in bugfix branch

- File: `api/index.py`
  - base64_to_number: changed to decode base64 bytes using little-endian byte order (`byteorder='little'`) per assignment specification.
  - number_to_base64: changed to encode integers to little-endian byte order and ensured that 0 is represented as a single zero byte (so base64 for 0 is not an empty string).

Rationale: The original implementation used big-endian when converting between integers and base64-encoded bytes, which caused mismatches with the assignment's requirement to use little-endian byte order. Tests were added in `tests/test_conversion.py` to assert little-endian roundtrips and to exercise all conversion endpoints and error cases.
