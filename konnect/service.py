"""
Service de paiement Konnect
Documentation officielle : https://developers.konnect.tn
"""
import hmac
import hashlib
import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class KonnectError(Exception):
    """Exception levée sur toute erreur Konnect."""
    pass


class KonnectPaymentService:

    CURRENCY = "TND"

    # ── Helpers internes ──────────────────────────────────────────────────────

    @classmethod
    def _base_url(cls) -> str:
        return getattr(
            settings,
            "KONNECT_API_URL",
            "https://api.konnect.network/api/v2",
        )

    @classmethod
    def _headers(cls) -> dict:
        return {
            "x-api-key":    settings.KONNECT_API_KEY,
            "Content-Type": "application/json",
        }

    # ── Initier un paiement ───────────────────────────────────────────────────

    @classmethod
    def init_payment(
        cls,
        partner,
        amount_millimes: int,
        description: str,
        order_ref: str,
        callback_url: str,
        webhook_url: str,
    ) -> dict:
        """
        Crée une session de paiement Konnect et retourne l'URL de paiement.

        Args:
            partner         : instance Partner (doit avoir email, phone, etc.)
            amount_millimes : montant en millimes  (ex : 50 TND → 50000)
            description     : texte affiché sur la page de paiement
            order_ref       : identifiant unique de la commande (str UUID)
            callback_url    : URL frontend de retour après paiement
            webhook_url     : URL backend pour la notification serveur

        Returns:
            { "payment_url": str, "payment_ref": str }
        """
        payload = {
            "receiverWalletId":       settings.KONNECT_WALLET_ID,
            "token":                  cls.CURRENCY,
            "amount":                 amount_millimes,
            "type":                   "immediate",
            "description":            description,
            "acceptedPaymentMethods": ["wallet", "bank_card", "e-DINAR"],
            "lifespan":               10,          # minutes avant expiration
            "checkoutForm":           True,
            "addPaymentFeesToAmount": False,
            "firstName":              getattr(partner, "contact_first_name", ""),
            "lastName":               getattr(partner, "contact_last_name", ""),
            "phoneNumber":            getattr(partner, "phone", ""),
            "email":                  getattr(partner, "email", ""),
            "orderId":                str(order_ref),
            "webhook":                webhook_url,
            "silentWebhook":          True,
            "successUrl":             f"{callback_url}?status=success&ref={order_ref}",
            "failUrl":                f"{callback_url}?status=failed&ref={order_ref}",
            "theme":                  "light",
        }

        try:
            response = requests.post(
                f"{cls._base_url()}/payments/init-payment",
                json=payload,
                headers=cls._headers(),
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            payment_ref = data.get("paymentRef")
            payment_url = data.get("payUrl")

            logger.info(
                "Konnect payment initiated | ref=%s | partner=%s",
                payment_ref, getattr(partner, "id", "?"),
            )

            return {"payment_url": payment_url, "payment_ref": payment_ref}

        except requests.HTTPError as e:
            logger.error("Konnect HTTP error [init_payment]: %s — %s", e, e.response.text)
            raise KonnectError(f"Erreur Konnect ({e.response.status_code}) : {e.response.text}")
        except requests.RequestException as e:
            logger.error("Konnect request error [init_payment]: %s", e)
            raise KonnectError(f"Impossible de contacter Konnect : {e}")

    # ── Vérifier un paiement ──────────────────────────────────────────────────

    @classmethod
    def verify_payment(cls, payment_ref: str) -> dict:
        """
        Interroge l'API Konnect pour connaître le statut d'un paiement.

        Returns:
            {
                "status":       "completed" | "pending" | "failed",
                "amount":       int,          # en millimes
                "completed_at": str | None,   # ISO datetime
            }
        """
        try:
            response = requests.get(
                f"{cls._base_url()}/payments/{payment_ref}",
                headers=cls._headers(),
                timeout=10,
            )
            response.raise_for_status()
            payment = response.json().get("payment", {})

            status_map = {
                "completed": "completed",
                "pending":   "pending",
                "failed":    "failed",
                "cancelled": "failed",
                "expired":   "failed",
            }

            return {
                "status":       status_map.get(payment.get("status"), "pending"),
                "amount":       payment.get("amount", 0),
                "completed_at": payment.get("updatedAt"),
            }

        except requests.HTTPError as e:
            logger.error("Konnect HTTP error [verify_payment]: %s", e)
            raise KonnectError(f"Erreur vérification paiement : {e}")
        except requests.RequestException as e:
            logger.error("Konnect request error [verify_payment]: %s", e)
            raise KonnectError(f"Impossible de vérifier le paiement : {e}")

    # ── Valider la signature webhook ──────────────────────────────────────────

    @classmethod
    def validate_webhook_signature(cls, payload_body: bytes, signature: str) -> bool:
        """
        Valide la signature HMAC-SHA256 envoyée par Konnect dans
        le header 'x-konnect-sign'.

        Args:
            payload_body : corps brut de la requête (request.body)
            signature    : valeur du header 'x-konnect-sign'

        Returns:
            True si la signature est valide, False sinon.
        """
        secret = settings.KONNECT_WEBHOOK_SECRET.encode("utf-8")
        expected = hmac.new(          # ← correction : hmac.new() est correct en Python
            secret,
            payload_body,
            hashlib.sha256,
        ).hexdigest()
        # compare_digest protège contre les timing attacks
        return hmac.compare_digest(expected, signature)

    # ── Dispatcher webhook ────────────────────────────────────────────────────

    @classmethod
    def handle_webhook(cls, payload: dict) -> None:
        """
        Point d'entrée unique pour traiter un événement webhook Konnect.

        Payload typique reçu de Konnect :
        {
            "type":       "payment:completed",
            "paymentRef": "xxx-yyy-zzz",
            "orderId":    "AD-<uuid>",
            "amount":     50000,
            "status":     "completed"
        }
        """
        event_type  = payload.get("type", "")
        payment_ref = payload.get("paymentRef", "")
        order_id    = payload.get("orderId", "")
        status      = payload.get("status", "")

        logger.info(
            "Konnect webhook received | type=%s | ref=%s | status=%s | order=%s",
            event_type, payment_ref, status, order_id,
        )

        if status == "completed":
            cls._on_payment_completed(payment_ref, order_id)
        elif status in ("failed", "cancelled", "expired"):
            cls._on_payment_failed(payment_ref, order_id, status)
        else:
            logger.warning("Konnect webhook: statut inconnu '%s'", status)

    # ── Handlers internes ─────────────────────────────────────────────────────

    @classmethod
    def _on_payment_completed(cls, payment_ref: str, order_id: str) -> None:
        """
        Paiement réussi → activer la publicité liée à la commande.
        order_id correspond à l'UUID de l'Advertisement.
        """
        from advertisements.models import Advertisement, AdStatus

        try:
            updated = Advertisement.objects.filter(
                id=order_id,
                status__in=[AdStatus.PENDING, AdStatus.REVIEW],
            ).update(status=AdStatus.ACTIVE)

            if updated:
                logger.info("Payment completed → ad activated | order=%s", order_id)
            else:
                logger.warning(
                    "Payment completed but no ad found/updated | order=%s", order_id
                )
        except Exception as e:
            logger.error(
                "Error activating ad after payment | order=%s | error=%s", order_id, e
            )

    @classmethod
    def _on_payment_failed(cls, payment_ref: str, order_id: str, status: str) -> None:
        """
        Paiement échoué / annulé / expiré → log et notification éventuelle.
        """
        logger.warning(
            "Payment %s | ref=%s | order=%s", status, payment_ref, order_id
        )
        # Optionnel : envoyer une notification email au partenaire
        # NotificationService.notify_payment_failed(order_id)