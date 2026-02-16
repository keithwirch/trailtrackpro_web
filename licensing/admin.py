from django.contrib import admin
from .models import License, LicenseActivation, Purchase


class LicenseActivationInline(admin.TabularInline):
    """Inline display of activations on the License admin page."""
    model = LicenseActivation
    extra = 0
    readonly_fields = ['machine_id', 'app_version', 'platform', 'activated_at', 'last_validated_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['key', 'email', 'is_revoked', 'active_activations_display', 'max_activations', 'purchase_link', 'expires_at', 'created_at']
    list_filter = ['is_revoked', 'created_at']
    search_fields = ['key', 'email', 'notes']
    readonly_fields = ['key', 'purchase_link', 'created_at']
    inlines = [LicenseActivationInline]
    
    fieldsets = (
        (None, {
            'fields': ('key', 'email', 'purchase_link')
        }),
        ('Status', {
            'fields': ('is_revoked', 'max_activations', 'expires_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['revoke_licenses', 'unrevoke_licenses']
    
    @admin.display(description='Active')
    def active_activations_display(self, obj):
        return f"{obj.active_activations_count}/{obj.max_activations}"

    @admin.display(description='Purchase')
    def purchase_link(self, obj):
        if hasattr(obj, 'purchase'):
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse("admin:licensing_purchase_change", args=[obj.purchase.id])
            return format_html('<a href="{}">{}</a>', url, obj.purchase)
        return "-"
    
    @admin.action(description='Revoke selected licenses')
    def revoke_licenses(self, request, queryset):
        count = queryset.update(is_revoked=True)
        self.message_user(request, f'{count} license(s) revoked.')
    
    @admin.action(description='Unrevoke selected licenses')
    def unrevoke_licenses(self, request, queryset):
        count = queryset.update(is_revoked=False)
        self.message_user(request, f'{count} license(s) unrevoked.')


@admin.register(LicenseActivation)
class LicenseActivationAdmin(admin.ModelAdmin):
    list_display = ['license', 'machine_id_short', 'platform', 'app_version', 'is_active', 'activated_at', 'last_validated_at']
    list_filter = ['is_active', 'platform', 'activated_at']
    search_fields = ['license__key', 'license__email', 'machine_id']
    readonly_fields = ['license', 'machine_id', 'app_version', 'platform', 'activated_at', 'last_validated_at']
    
    actions = ['deactivate_activations', 'reactivate_activations']
    
    @admin.display(description='Machine ID')
    def machine_id_short(self, obj):
        return f"{obj.machine_id[:12]}..."
    
    @admin.action(description='Deactivate selected activations')
    def deactivate_activations(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} activation(s) deactivated.')
    
    @admin.action(description='Reactivate selected activations')
    def reactivate_activations(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} activation(s) reactivated.')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['stripe_session_short', 'customer_email', 'amount_display', 'status', 'license_link', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['stripe_checkout_session_id', 'customer_email', 'license__key']
    readonly_fields = ['stripe_checkout_session_id', 'amount', 'currency', 'customer_email', 'license', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False
        
    @admin.display(description='Session ID')
    def stripe_session_short(self, obj):
        return f"{obj.stripe_checkout_session_id[:12]}..."
        
    @admin.display(description='Amount')
    def amount_display(self, obj):
        return f"{obj.amount / 100:.2f} {obj.currency.upper()}"
        
    @admin.display(description='License')
    def license_link(self, obj):
        if obj.license:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse("admin:licensing_license_change", args=[obj.license.id])
            return format_html('<a href="{}">{}</a>', url, obj.license.key)
        return "-"
