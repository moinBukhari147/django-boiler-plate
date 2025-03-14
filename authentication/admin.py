from django.contrib import admin
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin

################################################################
# Register your models here.

# =================================================================
# This is custom user model, which is used to create user with phone number as username
# Update the fields as per the requirement
User = get_user_model()
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("phone_number", "password",)}),
                    
        (_("Personal info"), {"fields": ("email","password_change", )}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone_number", "password1", "password2"),
            },
        ),
    )
    list_display = ("phone_number","email","otp","otp_attempt", "new_number","password_change", "is_active", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups") # add the fields which you want to use as filter
    search_fields = ( "email", "phone_number") # add the fields which you want to use as search
    ordering = ("phone_number",)
    

# =================================================================
# Registering all models collectively.
app_models = apps.get_app_config('authentication').get_models()
for model in app_models:
    if model.__name__ == User.__name__:
        continue
    model_name = model.__name__+"Admin"
    @admin.register(model)
    class ModelAdmin(admin.ModelAdmin):
        list_display = [field.name for field in model._meta.fields]
        # search_fields = ("user__phone_number",)
        class Meta:
            verbose_name = model.__name__

    ModelAdmin.__name__ = model_name  

# =================================================================
# Register models with custom settings like that of user.
# 