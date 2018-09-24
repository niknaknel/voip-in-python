import pickle

class Header:
    def __init__(self, msg_type, src_ip):
        self.msg_type = msg_type
        self.src_ip = src_ip

    def serialize(self):
        return pickle.dumps(self, -1)

    @classmethod
    def deserialize(cls, serial):
        h = pickle.loads(serial)

        return cls(h.msg_type, h.src_ip)

    def __str__(self):
        return """
        msg_type: {0}
        src_ip:    {1}
        ---------------------------------
        """.format(self.msg_type, self.src_ip)