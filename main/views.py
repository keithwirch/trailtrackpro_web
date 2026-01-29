from django.shortcuts import render

def terms_of_use(request):
    return render(request, 'legal/terms-of-use.html')

def privacy_policy(request):
    return render(request, 'legal/privacy-policy.html')
