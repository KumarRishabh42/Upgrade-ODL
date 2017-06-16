class WgetError(Exception):
    def __init__(self, message):
        super(WgetError, self).__init__(message)
