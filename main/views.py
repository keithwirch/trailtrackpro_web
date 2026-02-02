from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def terms_of_use(request):
    return render(request, 'legal/terms-of-use.html')

def privacy_policy(request):
    return render(request, 'legal/privacy-policy.html')

# Placeholder views for future marketing pages
def features(request):
    return render(request, 'features.html', {'page_title': 'Features'})

def pricing(request):
    return render(request, 'pricing.html')

def contact(request):
    return render(request, 'placeholder.html', {'page_title': 'Contact'})

def purchase(request):
    return render(request, 'purchase.html')
