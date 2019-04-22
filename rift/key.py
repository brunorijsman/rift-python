import hmac

ALGORITHMS = ["hmac-sha-1", "hmac-sha-256"]

class Key:

    def __init__(self, key_id, algorithm, secret):
        assert algorithm in ALGORITHMS
        self.key_id = key_id
        self.algorithm = algorithm
        self.secret = secret

    def digest(self, message_parts):
        if self.algorithm == "hmac-sha-1":
            digestmod = "sha1"
        elif self.algorithm == "hmac-sha-256":
            digestmod = "sha256"
        else:
            assert False
        the_hmac = hmac.new(self.secret.encode(), digestmod=digestmod)
        for message_part in message_parts:
            if message_part is not None:
                the_hmac.update(message_part)
        return the_hmac.digest()

    def padded_digest(self, message_parts):
        dig = self.digest(message_parts)
        if len(dig) % 4 != 0:
            dig += b'\x00' * (4 - len(dig) % 4)
        return dig
