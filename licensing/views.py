import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import License, LicenseActivation


def json_error(error_code, message, status=200):
    """Return a standardized error response."""
    return JsonResponse({
        'success': False,
        'error': error_code,
        'message': message
    }, status=status)


def validate_uuid(value):
    """Check if a string is a valid UUID."""
    import uuid
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


@csrf_exempt
@require_POST
def activate_license(request):
    """
    Activate a license key on a specific machine.
    
    POST /api/license/activate/
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('INVALID_REQUEST', 'Invalid JSON body')
    
    license_key = data.get('license_key', '').strip()
    machine_id = data.get('machine_id', '').strip()
    app_version = data.get('app_version', '').strip()
    platform = data.get('platform', '').strip()
    
    # Validate required fields
    if not all([license_key, machine_id, app_version, platform]):
        return json_error('INVALID_REQUEST', 'Missing required fields')
    
    # Validate UUID format
    if not validate_uuid(license_key):
        return json_error('INVALID_KEY', 'License key format is invalid')
    
    # Find the license
    try:
        license = License.objects.get(key=license_key)
    except License.DoesNotExist:
        return json_error('INVALID_KEY', 'License key does not exist')
    
    # Check if revoked
    if license.is_revoked:
        return json_error('INVALID_KEY', 'This license has been revoked')
    
    # Check expiry
    if license.expires_at and license.expires_at < timezone.now():
        return json_error('EXPIRED', 'This license has expired')
    
    # Check if already exists for this machine (active or inactive)
    activation = LicenseActivation.objects.filter(
        license=license,
        machine_id=machine_id
    ).first()
    
    if activation:
        if not activation.is_active:
             # If reactivating, we must check limits
             if not license.can_activate:
                return json_error(
                    'ALREADY_ACTIVATED', 
                    'This license is already activated on another machine'
                )
             activation.is_active = True

        # Update metadata for both active and reactivated
        activation.app_version = app_version
        activation.platform = platform
        activation.save()
        
        return JsonResponse({
            'success': True,
            'license': {'email': license.email}
        })
    
    # New activation
    if not license.can_activate:
        return json_error(
            'ALREADY_ACTIVATED', 
            'This license is already activated on another machine'
        )
    
    LicenseActivation.objects.create(
        license=license,
        machine_id=machine_id,
        app_version=app_version,
        platform=platform
    )
    
    return JsonResponse({
        'success': True,
        'license': {'email': license.email}
    })


@csrf_exempt
@require_POST
def validate_license(request):
    """
    Validate an existing license activation.
    Called silently every 7 days by the app.
    
    POST /api/license/validate/
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'error': 'INVALID_REQUEST'})
    
    license_key = data.get('license_key', '').strip()
    machine_id = data.get('machine_id', '').strip()
    
    if not all([license_key, machine_id]):
        return JsonResponse({'valid': False, 'error': 'INVALID_REQUEST'})
    
    if not validate_uuid(license_key):
        return JsonResponse({'valid': False, 'error': 'INVALID_KEY'})
    
    # Find the license
    try:
        license = License.objects.get(key=license_key)
    except License.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'INVALID_KEY'})
    
    # Check if revoked
    if license.is_revoked:
        return JsonResponse({'valid': False, 'error': 'LICENSE_REVOKED'})
    
    # Check expiry
    if license.expires_at and license.expires_at < timezone.now():
        return JsonResponse({'valid': False, 'error': 'EXPIRED'})
    
    # Find the activation
    activation = LicenseActivation.objects.filter(
        license=license,
        machine_id=machine_id,
        is_active=True
    ).first()
    
    if not activation:
        return JsonResponse({
            'valid': False, 
            'error': 'NOT_ACTIVATED',
            'message': 'This license is not activated on this machine'
        })
    
    # Update last_validated_at (auto_now handles this on save)
    activation.save()
    
    return JsonResponse({'valid': True})


@csrf_exempt
@require_POST
def deactivate_license(request):
    """
    Deactivate a license from the current machine.
    Allows transfer to another device.
    
    POST /api/license/deactivate/
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON body'})
    
    license_key = data.get('license_key', '').strip()
    machine_id = data.get('machine_id', '').strip()
    
    if not all([license_key, machine_id]):
        return JsonResponse({'success': False, 'message': 'Missing required fields'})
    
    if not validate_uuid(license_key):
        return JsonResponse({'success': False, 'message': 'Invalid license key format'})
    
    # Find the license
    try:
        license = License.objects.get(key=license_key)
    except License.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'License not found'})
    
    # Find and deactivate the activation
    activation = LicenseActivation.objects.filter(
        license=license,
        machine_id=machine_id,
        is_active=True
    ).first()
    
    if not activation:
        return JsonResponse({
            'success': False, 
            'message': 'No active activation found for this machine'
        })
    
    activation.is_active = False
    activation.save()
    
    return JsonResponse({'success': True})
