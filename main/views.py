from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import stripe
from licensing.models import Purchase, License

stripe.api_key = settings.STRIPE_SECRET_KEY

def index(request):
    return render(request, 'index.html', {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })

def terms_of_use(request):
    return render(request, 'legal/terms-of-use.html')

def privacy_policy(request):
    return render(request, 'legal/privacy-policy.html')

# Placeholder views for future marketing pages
def features(request):
    return render(request, 'features.html', {'page_title': 'Features'})

def pricing(request):
    return render(request, 'pricing.html', {
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })

def create_checkout_session(request):
    if request.method == 'POST':
        try:
            domain_url = request.build_absolute_uri('/')[:-1] # Remove trailing slash
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': settings.STRIPE_PRICE_ID,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=domain_url + reverse('success') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + reverse('cancel'),
                customer_email=request.POST.get('email'), # Optional: prefill if available
            )
            
            # Create pending purchase
            Purchase.objects.create(
                stripe_checkout_session_id=checkout_session.id,
                amount=checkout_session.amount_total,
                currency=checkout_session.currency,
                status='pending'
            )
            
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=403)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('purchase')
        
    try:
        purchase = Purchase.objects.get(stripe_checkout_session_id=session_id)
        
        # In a real app, verify with Stripe API again or use webhooks
        # For this implementation, we'll verify status if pending
        if purchase.status == 'pending':
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                purchase.status = 'completed'
                purchase.customer_email = session.customer_details.email
                
                # Generate License
                if not purchase.license:
                    license = License.objects.create(email=purchase.customer_email)
                    purchase.license = license
                
                purchase.save()
            
    except Purchase.DoesNotExist:
        pass # Handle error or show generic success
        
    return render(request, 'success.html', {'purchase': purchase})

def cancel(request):
    return render(request, 'cancel.html')
