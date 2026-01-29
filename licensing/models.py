import uuid
from django.db import models


class License(models.Model):
    """
    Represents a software license for TrailTrack Pro.
    """
    key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(help_text="Customer email address")
    
    # Status
    is_revoked = models.BooleanField(default=False, help_text="Revoke to block this license")
    max_activations = models.PositiveIntegerField(default=1, help_text="Maximum simultaneous activations allowed")
    
    # Optional expiry
    expires_at = models.DateTimeField(blank=True, null=True, help_text="Leave blank for perpetual license")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Internal notes about this license")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.key} ({self.email})"

    @property
    def active_activations_count(self):
        """Number of currently active activations."""
        return self.activations.filter(is_active=True).count()

    @property
    def can_activate(self):
        """Check if a new activation is allowed."""
        return self.active_activations_count < self.max_activations


class LicenseActivation(models.Model):
    """
    Tracks individual machine activations for a license.
    """
    license = models.ForeignKey(
        License, 
        on_delete=models.CASCADE, 
        related_name='activations'
    )
    machine_id = models.CharField(max_length=64, help_text="SHA256 hash of hostname (32 chars)")
    app_version = models.CharField(max_length=20)
    platform = models.CharField(max_length=20, help_text="win32, darwin, or linux")
    
    # Timestamps
    activated_at = models.DateTimeField(auto_now_add=True)
    last_validated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-activated_at']
        # A machine can only have one activation per license
        unique_together = ['license', 'machine_id']

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.license.key} on {self.machine_id[:8]}... ({status})"
