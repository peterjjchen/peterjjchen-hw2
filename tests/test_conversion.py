import base64
import json
import pytest

from api import index


# Helper: encode integer to base64 using little-endian byte order (per assignment spec)
def to_b64_le(n: int) -> str:
    if n == 0:
        return base64.b64encode((0).to_bytes(1, byteorder='little')).decode('utf-8')
    byte_count = (n.bit_length() + 7) // 8
    b = n.to_bytes(byte_count, byteorder='little')
    return base64.b64encode(b).decode('utf-8')


def from_b64_le(s: str) -> int:
    b = base64.b64decode(s)
    return int.from_bytes(b, byteorder='little')


@pytest.mark.parametrize("text,expected", [
    ("zero", 0),
    ("one", 1),
    ("two", 2),
    ("ten", 10),
])
def test_text_to_number_basic(text, expected):
    assert index.text_to_number(text) == expected


def test_text_to_number_invalid():
    with pytest.raises(ValueError):
        index.text_to_number("one hundred")


@pytest.mark.parametrize("n,bin_s,oct_s,dec_s,hex_s", [
    (0, "0", "0", "0", "0"),
    (1, "1", "1", "1", "1"),
    (10, "1010", "12", "10", "a"),
    (255, "11111111", "377", "255", "ff"),
])
def test_number_string_formats(n, bin_s, oct_s, dec_s, hex_s):
    assert format(n, 'b') == bin_s
    assert format(n, 'o') == oct_s
    assert str(n) == dec_s
    assert format(n, 'x') == hex_s


def test_base64_little_endian_roundtrip():
    n = 0x010203
    b64_le = to_b64_le(n)
    # number_to_base64 should produce little-endian encoding
    got_b64 = index.number_to_base64(n)
    assert got_b64 == b64_le

    # base64_to_number should decode little-endian base64
    decoded = index.base64_to_number(b64_le)
    assert decoded == n


@pytest.mark.parametrize("b64_str", ["!!invalid!!", "123"])
def test_base64_to_number_invalid(b64_str):
    with pytest.raises(ValueError):
        index.base64_to_number(b64_str)


# Test full convert endpoint flows using Flask test client
@pytest.fixture
def client():
    index.app.config['TESTING'] = True
    with index.app.test_client() as client:
        yield client


@pytest.mark.parametrize("input_type,input_value,output_type,expected", [
    ("decimal", "255", "binary", "11111111"),
    ("binary", "1010", "decimal", "10"),
    ("hexadecimal", "ff", "decimal", "255"),
    ("octal", "377", "decimal", "255"),
    ("text", "one", "decimal", "1"),
])
def test_convert_endpoint_basic(client, input_type, input_value, output_type, expected):
    payload = {
        'input': input_value,
        'inputType': input_type,
        'outputType': output_type
    }
    rv = client.post('/convert', data=json.dumps(payload), content_type='application/json')
    data = rv.get_json()
    assert data['error'] is None
    assert data['result'] == expected


def test_convert_endpoint_base64_le(client):
    # send base64 in little-endian for number 0x010203
    n = 0x010203
    b64_le = to_b64_le(n)
    payload = {
        'input': b64_le,
        'inputType': 'base64',
        'outputType': 'decimal'
    }
    rv = client.post('/convert', data=json.dumps(payload), content_type='application/json')
    data = rv.get_json()
    # index.base64_to_number currently decodes big-endian; ensure our tests check for expected spec
    assert data['error'] is None
    assert int(data['result']) == n


def test_convert_endpoint_invalid_input_type(client):
    payload = {'input': '1', 'inputType': 'unknown', 'outputType': 'decimal'}
    rv = client.post('/convert', data=json.dumps(payload), content_type='application/json')
    data = rv.get_json()
    assert data['result'] is None
    assert 'Invalid input type' in data['error']


def test_convert_endpoint_invalid_output_type(client):
    payload = {'input': '1', 'inputType': 'decimal', 'outputType': 'unknown'}
    rv = client.post('/convert', data=json.dumps(payload), content_type='application/json')
    data = rv.get_json()
    assert data['result'] is None
    assert 'Invalid output type' in data['error']
