class WgetError(Exception):
    def __init__(self, message):
        super(WgetError, self).__init__(message)

class TimeoutError(Exception):
    def __init__(self, message):
        super(TimeoutError, self).__init__(message)
