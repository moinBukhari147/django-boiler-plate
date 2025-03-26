import uuid

from django.contrib.auth.models import AbstractUser
from datetime import date
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator
from functools import partial
from .custom_manager import custom_user_manager

from django.utils.translation import gettext_lazy as _
from utils import models_validators as m_valid
from utils import models_choices as m_choices

################################################################
# MODELS

# =================================================================
# This is custom user model, which is used to create user with phone number as username
# Update the fields as per the requirement
class User(AbstractUser):
    id = None
    uuid = models.UUIDField(_("uuid"),default=uuid.uuid4, primary_key=True)
    phone_number = models.BigIntegerField(_("phone number"),
        validators=[MinValueValidator(3000000000), MaxValueValidator(3999999999)],
        unique=True,
        null=False,
        error_messages={
            "unique": _("This number is already registered against a user."),
        },
    )
    new_number = models.BigIntegerField(_("new number"),
        validators=[MinValueValidator(3000000000), MaxValueValidator(3499999999)],
        unique=True,
        null=True,
        default= None,
        error_messages={
            "unique": _("This number is already registered against a user."),
        },
    )
    email = models.EmailField(_("email address"), unique=True, null=True, default=None)
    otp = models.IntegerField(null=True, default=None)
    otp_attempt = models.IntegerField(default=0)
    password_change = models.BooleanField(_("can change password"),default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    
    username = None
    first_name = None
    last_name = None
    

    objects = custom_user_manager()
    USERNAME_FIELD = "phone_number" # This is the field which will be used to login
    REQUIRED_FIELDS = [] # These are the fields which are required to create a user
    def __str__(self) -> str:
        return str(self.phone_number)