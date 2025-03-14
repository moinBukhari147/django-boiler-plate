from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.apps import apps
from django.utils.translation import gettext_lazy as _


# Custom User Manager
class custom_user_manager(UserManager):
    def _create_user(self, phone_number, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not phone_number:
            raise ValueError("The given phone number must be set")
        if not password:
            raise ValueError("The given password must be set")
        if email:
            email = self.normalize_email(email)
        
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self,phone_number , email=None, password=None, **extra_fields):
        # check if the user explicitely provide the value is_active = True than what happened, does it set the value to True, if so than its a buf.
        
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_staff", False)
        return self._create_user(phone_number, email, password, **extra_fields)
    
    def create_superuser(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, email, password, **extra_fields)
    