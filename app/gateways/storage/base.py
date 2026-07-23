

class StorageError(Exception):
    pass


class StorageGateway:

    def save(self, org_id, key, data):
        raise NotImplementedError

    def read(self, ref):
        raise NotImplementedError

    def exists(self, ref):
        raise NotImplementedError

    def url(self, ref):
        return None
