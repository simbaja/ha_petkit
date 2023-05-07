
class PetkitError(Exception):
    """ Base class for all other custom exceptions """
    pass

class PetkitAuthFailedError(PetkitError):
    """Error raised when the client failed to authenticate"""
    pass

class PetkitServerError(PetkitError):
    """Error raised when there is a server error (not 4xx http code)"""
    pass