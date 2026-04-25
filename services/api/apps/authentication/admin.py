from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import User


class CryptopusUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")


class CryptopusUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "email", "first_name", "last_name",
            "dob", "phone_number",
            "address", "city", "country", "postal_code",
            "role", "account_status",
        )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CryptopusUserCreationForm
    form = CryptopusUserChangeForm
    model = User

    list_display = (
        "email", "first_name", "last_name", "role", "account_status",
        "email_verified", "otp_enabled", "is_staff",
    )
    list_filter = (
        "role", "account_status", "email_verified", "otp_enabled",
        "is_staff", "is_superuser",
    )
    search_fields = ("email", "first_name", "last_name", "phone_number", "city", "country")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "dob", "phone_number")}),
        ("Address", {"fields": ("address", "city", "country", "postal_code")}),
        ("Login status", {"fields": ("account_status", "email_verified", "otp_enabled", "otp_secret")}),
        ("Role & permissions", {"fields": ("role", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("last_login", "created_at", "deleted_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )
    readonly_fields = ("created_at", "last_login")

    actions = [
        "mark_email_verified",
        "reset_otp",
        "activate_account",
        "suspend_account",
        "force_logout",
    ]

    @admin.action(description="Mark email as verified")
    def mark_email_verified(self, request, queryset):
        updated = queryset.update(email_verified=True)
        self.message_user(request, f"{updated} user(s) marked as email-verified.", messages.SUCCESS)

    @admin.action(description="Reset OTP (user must set up again)")
    def reset_otp(self, request, queryset):
        updated = queryset.update(otp_enabled=False, otp_secret=None)
        self.message_user(request, f"OTP reset for {updated} user(s).", messages.SUCCESS)

    @admin.action(description="Activate account")
    def activate_account(self, request, queryset):
        updated = queryset.update(account_status=User.AccountStatus.ACTIVE)
        self.message_user(request, f"{updated} account(s) activated.", messages.SUCCESS)

    @admin.action(description="Suspend account")
    def suspend_account(self, request, queryset):
        updated = queryset.update(account_status=User.AccountStatus.SUSPENDED)
        self.message_user(request, f"{updated} account(s) suspended.", messages.WARNING)

    @admin.action(description="Force logout (blacklist all refresh tokens)")
    def force_logout(self, request, queryset):
        count = 0
        for user in queryset:
            for token in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=token)
                count += 1
        self.message_user(request, f"Blacklisted {count} refresh token(s).", messages.SUCCESS)