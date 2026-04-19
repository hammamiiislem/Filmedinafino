class DomainException(Exception):
    """Base pour toutes les erreurs métier (ex: Email déjà vérifié)"""
    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(DomainException):
    """Erreurs liées au login/token"""
    pass