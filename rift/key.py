ALGORITHMS = ["md5", "sha256", "sha512"]

class Key:

    def __init__(self, key_id, algorithm, secret):
        assert algorithm in ALGORITHMS
        self.key_id = key_id
        self.algorithm = algorithm
        self.secret = secret
