"""
Webhook Konnect — reçoit les notifications de paiement serveur-à-serveur.

Ajouter dans core/urls.py :
    from konnect.views import konnect_webhook
    path("api/konnect/webhook/", konnect_webhook, name="konnect-webhook"),
"""
import json
import logging

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .service import KonnectPaymentService, KonnectError

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def konnect_webhook(request):
    """
    Endpoint POST appelé par Konnect après chaque événement de paiement.

    Flux :
        1. Valider la signature HMAC-SHA256 (header x-konnect-sign)
        2. Parser le JSON
        3. Dispatcher vers KonnectPaymentService.handle_webhook()
        4. Retourner 200 OK → Konnect ne retentera pas la notification
    """

    # ── 1. Vérification de la signature ──────────────────────────────────────
    signature = request.headers.get("x-konnect-sign", "")

    if not signature:
        logger.warning("Konnect webhook: header 'x-konnect-sign' manquant")
        return HttpResponseBadRequest("Header de signature manquant.")

    if not KonnectPaymentService.validate_webhook_signature(request.body, signature):
        logger.warning("Konnect webhook: signature HMAC invalide")
        return HttpResponseBadRequest("Signature invalide.")

    # ── 2. Parse du payload JSON ──────────────────────────────────────────────
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError as e:
        logger.error("Konnect webhook: JSON invalide — %s", e)
        return HttpResponseBadRequest("Corps JSON invalide.")

    # ── 3. Traitement de l'événement ──────────────────────────────────────────
    try:
        KonnectPaymentService.handle_webhook(payload)
        return JsonResponse({"status": "ok"})

    except KonnectError as e:
        logger.error("Konnect webhook KonnectError: %s", e)
        # On retourne 200 quand même pour éviter les retries Konnect
        # mais on logue l'erreur pour investigation
        return JsonResponse({"status": "error", "message": str(e)}, status=200)

    except Exception as e:
        logger.exception("Konnect webhook unexpected error: %s", e)
        return JsonResponse({"status": "error", "message": "Erreur interne."}, status=500)