import strawberry
from .services import EmailVerificationService
from core.exceptions import DomainException
# classe pour les payloads des utilisateurs --------------------------------------------------------
@strawberry.type
class VerificationPayload:
    success: bool
    message: str
# --------------------------------------------------------

@strawberry.type
class Mutation:
    # verifier le token 
    @strawberry.mutation
    def verify_email(self, token: str) -> VerificationPayload:
        try:
            EmailVerificationService.verify_email(token)
            return VerificationPayload(
                success=True, 
                message="Compte activé !"
            )
        except DomainException as e:
            return VerificationPayload(
                success=False, 
                message=str(e)
            )
         # envoie de nouveau token   
    @strawberry.mutation
    def resend_verification_email(self, email: str) -> VerificationPayload:
        # On utilise le service qui est enumeration-safe
        EmailVerificationService.resend_verification(email)
        return VerificationPayload(
            success=True,
            message="Si un compte existe, un email a été envoyé."
        )