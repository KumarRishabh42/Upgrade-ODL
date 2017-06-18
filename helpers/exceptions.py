class WgetError(Exception):
    def __init__(self, message):
        super(WgetError, self).__init__(message)

class TimedoutError(Exception):
    def __init__(self, message):
        super(TimedoutError, self).__init__(message)
