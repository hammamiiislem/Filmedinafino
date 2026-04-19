from functools import wraps
from .exceptions import DomainException

def handle_service_errors(func):
    """
    Décorateur pour les méthodes de service.
    Il intercepte les DomainException et s'assure qu'elles sont 
    traitées comme des erreurs métier et non comme des crashs serveurs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # On essaie d'exécuter la fonction de service (ex: create_user)
            return func(*args, **kwargs)
        
        except DomainException as e:
            # Si c'est une erreur métier que NOUS avons définie
            # On peut la logger ici si besoin
            print(f"[SERVICE ERROR] {e.code}: {e.message}")
            # On la relève pour que le resolver GraphQL puisse la capturer 
            # et la mettre dans le champ 'errors' de ta MutationResponse
            raise e
            
        except Exception as e:
            # Si c'est une erreur inattendue (Bug, DB down, etc.)
            # On log l'erreur réelle pour le développeur
            print(f"[UNEXPECTED ERROR] {str(e)}")
            # On lève une exception générique pour ne pas fuiter d'infos sensibles
            raise DomainException(
                message="Une erreur interne est survenue.",
                code="INTERNAL_SERVER_ERROR"
            )
            
    return wrapper