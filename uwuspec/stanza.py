import enum
import json


class StanzaDecodeError(ValueError):
    pass


class Variant(enum.Enum):
    Message = enum.auto()
    Error = enum.auto()
    Hello = enum.auto()
    Bye = enum.auto()
    Unknown = enum.auto()


class Stanza:
    END = b'}'
    ENCODING = "utf8"
    ENCODING_ERRORS = "backslashreplace" # TODO : figure out if "namereplace" is better
    VARIANT_FILTER = (
        (("from", "to", "body"), Variant.Message),
        (("error", "reason"), Variant.Error),
        (("hello"), Variant.Hello),
        (("bye"), Variant.Bye)
    )

    def __init__(self, data):
        self.hive: dict
        self.data: bytes
        self.variant = Variant.Unknown

        if type(data) is dict:
            self.hive = data
            self.data = self.to_bytes()
        elif type(data) is bytes:
            try:
                self.data = data
                self.hive = json.loads(data)
            except (json.JSONDecodeError):
                raise StanzaDecodeError
        else:
            raise TypeError("data must be a dict or bytes")

        # TODO : maybe have a "variant" key and just validate that
        for keys, variant in self.VARIANT_FILTER:
            if all(key in self.hive for key in keys):
                # found the variant!
                self.variant = variant
                break

    def __getitem__(self, key: str):
        return self.hive[key]

    def to_bytes(self) -> bytes:
        return json.dumps(self.hive).encode(self.ENCODING, self.ENCODING_ERRORS)