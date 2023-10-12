import hashlib
import hmac

ALGORITHM_TO_DIGESTMOD = {
    "null": "null",                 # Returns an empty digest; used for special key-id 0
    "hmac-sha-1": "sha1",           # HMAC-SHA-xxx(secret, payload) digest
    "hmac-sha-224": "sha224",
    "hmac-sha-256": "sha256",
    "hmac-sha-384": "sha384",
    "hmac-sha-512": "sha512",
    "sha-1": "sha1",                # SHA-xxx(secret + payload) digest
    "sha-224": "sha224",
    "sha-256": "sha256",
    "sha-384": "sha384",
    "sha-512": "sha512",
}

ALGORITHMS = list(ALGORITHM_TO_DIGESTMOD.keys())

class Key:

    def __init__(self, key_id, algorithm, secret):
        assert algorithm in ALGORITHMS
        self.key_id = key_id
        self.algorithm = algorithm
        self.secret = secret

    def digest(self, message_parts):
        if self.key_id == 0:
            assert self.algorithm == "null"
            return b''
        elif "hmac" in self.algorithm:
            assert self.algorithm in ALGORITHMS
            digestmod = ALGORITHM_TO_DIGESTMOD[self.algorithm]
            the_hmac = hmac.new(self.secret.encode(), digestmod=digestmod)
            for message_part in message_parts:
                if message_part is not None:
                    the_hmac.update(message_part)
            return the_hmac.digest()
        else:
            assert self.algorithm in ALGORITHMS
            digestmod = ALGORITHM_TO_DIGESTMOD[self.algorithm]
            the_hash = hashlib.new(name=digestmod)
            the_hash.update(self.secret.encode())
            for message_part in message_parts:
                if message_part is not None:
                    the_hash.update(message_part)
            return the_hash.digest()

    def padded_digest(self, message_parts):
        dig = self.digest(message_parts)
        if len(dig) % 4 != 0:
            dig += b'\x00' * (4 - len(dig) % 4)
        return dig
