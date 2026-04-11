"""
Webhook Konnect — POST /api/konnect/webhook/
Ajouter dans core/urls.py :
    path("api/konnect/webhook/", konnect_webhook),
"""
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .service import KonnectPaymentService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def konnect_webhook(request):
    # 1. Valider la signature HMAC
    signature = request.headers.get("x-konnect-sign", "")
    if not KonnectPaymentService.validate_webhook_signature(request.body, signature):
        logger.warning("Konnect webhook: signature invalide")
        return HttpResponseBadRequest("Signature invalide")

    # 2. Parser le payload
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON invalide")

    # 3. Traiter
    try:
        KonnectPaymentService.handle_webhook(payload)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)