from django.shortcuts import redirect
from django.urls import reverse

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile:
                # 1. First Login Password Change Force
                allow_list = [
                    reverse('shared:logout'),
                    # Add password change URL here once created
                    # reverse('shared:password_change'), 
                ]
                
                # Check if we are already on an allowed path to avoid loops
                path = request.path
                
                # if profile.is_first_login and path not in allow_list and not path.startswith('/admin/'):
                #     return redirect('shared:password_change')

                # 2. Subscription Check
                # Skip check for staff/admin
                if not profile.is_staff_type:
                    # Logic: if expired, set is_active_account to False
                    if profile.subscription_days_left is not None and profile.subscription_days_left < 0:
                        if profile.is_active_account:
                            profile.is_active_account = False
                            profile.save(update_fields=['is_active_account'])
                    
                    # Redirect if inactive
                    subscribe_url = reverse('guard:dashboard') # Placeholder until subscribe page is ready
                    if not profile.is_active_account and path != subscribe_url and not path.startswith('/static/'):
                         # For now, let's just warn or redirect to a landing page
                         pass

        response = self.get_response(request)
        return response
