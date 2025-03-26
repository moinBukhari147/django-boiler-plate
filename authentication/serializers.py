import random
import os


from rest_framework.exceptions import AuthenticationFailed
from django.core import exceptions as django_exceptions
from django.contrib.auth import get_user_model, authenticate
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from . import models as m
from rest_framework import serializers
from utils import response as res
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings
from django.db import IntegrityError, transaction
from django.contrib.auth.password_validation import validate_password



###################################################################
                            # SERIALIZERS
###################################################################


User = get_user_model()
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    class Meta:
        model = User
        fields = ("uuid","phone_number", "email", "password", "is_active", )
        extra_kwargs = {
            "is_active": {"read_only": True},
        } 


    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get("password")
            
        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError({"password":serializer_error["non_field_errors"]})  
        # number is also stored in new number to prevent writing the two OTP verifier for both userCreate and ChangeNumber
        attrs['new_number']= attrs.get('phone_number')
        
        # creating and assigining the OTP
        otp = random.randint(100010, 999989)
        attrs["otp"]= otp
        return attrs


    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)
        except IntegrityError as e:
            self.fail(f"Error raised while creating the user.${str(e)}")
        return user


# =====================================================================  
class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("uuid","email","is_active", "phone_number")
        extra_kwargs = {
            "email": {"required": True},
            "is_active": {"read_only": True},
            "phone_number": {"read_only": True},
            "uuid": {"read_only": True},
        }
     # Customize the update method to update the user as per the requirement
    def update(self, instance, validated_data):
        if validated_data.get('email'):
            instance.email = validated_data.get('email', instance.email)
            instance.save()
        return instance
    
# =====================================================================
# This serializer is used for both
# OTP verification of the newly creted user phone number
# OTP verification of the user phone number change
class VerifyOtpSerialzer(serializers.Serializer):
    otp = serializers.IntegerField(min_value = 100010,max_value =999989, error_messages={"min_value": "OTP must contain min 6 digits.", "max_value": "OTP must contain max 6 digits."})
    uuid = serializers.UUIDField(error_messages={"invalid": "Invalid UUID. Manage it from frontend."})
    
    def validate(self, attrs):
        # Rasing the validation error with in the transaction.atomic block will rollback the transaction
        # So the error is stored in the error_obj and raised at the end of the block during wrong OTP attempt.
        error_obj = {}
        try:
            with transaction.atomic():
                user_uuid = attrs.get('uuid')
                otp = attrs.get('otp')
                # select_for_update is used to lock the row until the transaction is completed
                user = User.objects.select_for_update().filter(uuid = user_uuid).only("phone_number", "new_number", "otp", "otp_attempt", "is_active").first()
                
                if user is None:
                    raise serializers.ValidationError({"message": "User not found, invalid uuid."}, code="frontend")

                if not user.new_number:
                    raise res.ConflictError({"message": "Number is already verified."})
                
                if not user.otp:
                    raise serializers.ValidationError({"message": "OTP is not send to this number. Generate OTP first."})
                if user.otp ==otp:
                    user.phone_number = user.new_number
                    user.new_number = None
                    user.otp = None
                    user.otp_attempt = 0
                    # For newly created user
                    if not user.is_active:
                        user.is_active = True
                        refresh = RefreshToken.for_user(user)
                        tokens = {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        }
                        attrs['tokens'] = tokens
                    # update_fields is used to update only the required fields
                    user.save(update_fields=["phone_number", "new_number", "otp", "otp_attempt", "is_active"])
                    return attrs
                else:
                    if user.otp_attempt<2:
                        user.otp_attempt = user.otp_attempt+1
                        user.save(update_fields=["otp_attempt"])
                        error_obj = {"otp": "Wrong OTP."}
                    else:
                        user.otp = None
                        user.otp_attempt = 0
                        user.save(update_fields=["otp", "otp_attempt"])
                        error_obj = {"otp": "Expired, resend OTP"}
                    
        except IntegrityError as e:
            raise serializers.ValidationError({"message": str(e)})
        raise serializers.ValidationError(error_obj)
        

# =====================================================================
class ResendOtpSerializer(serializers.Serializer):
    phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
    def validate(self, attrs):
        number = attrs.get('phone_number')
        user = User.objects.filter(new_number= number).first()
        if not user:
            raise serializers.ValidationError({"phone_number": "This number is not regiestered against any user."}, code="frontend")
        otp = random.randint(100010, 999989)
        user.otp = otp
        user.save(update_fields=["otp"])
        attrs['otp'] = otp
        return attrs
    
# =====================================================================
class ChangeNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["phone_number"]

    def validate(self, attrs):
        user = self.context.get("user")
        if user.phone_number == attrs.get("phone_number"):
            raise serializers.ValidationError({"phone_number": "New number is same as old number."})
        return attrs
    def update(self, instance, validated_data):
        instance.new_number = validated_data.get('phone_number', instance.new_number)
        instance.otp = random.randint(100010, 999989)
        instance.save(update_fields=["new_number", "otp"])
        return instance

class ForgetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
    def validate(self, attrs):
        number = attrs.get('phone_number')
        user = User.objects.filter(phone_number= number).only("uuid").first()
        if not user:
            raise serializers.ValidationError({"phone_number": "This number is not regiestered against any user."})
        otp = random.randint(100010, 999989)
        user.otp = otp
        user.otp_attempt = 0
        user.save(update_fields=["otp", "otp_attempt"])
        return attrs
    
# =====================================================================
class ForgetPasswordOtpVerifySerializer(serializers.Serializer):
    phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
    otp = serializers.IntegerField(min_value = 100010,max_value =999989)
    error_obj = {}
    def validate(self, attrs):
        number = attrs.get('phone_number')
        otp = attrs.get('otp')
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().filter(phone_number = number).only("uuid", "otp", "otp_attempt", "password_change").first()
                if not user:
                    raise serializers.ValidationError(
                        {"phone_number":"No user is registered against this number."}, code="frontend")
                if not user.otp:
                    raise serializers.ValidationError({"message": "OTP is not send to this number. Generate OTP first"}, code="frontend")
                
                if user.otp ==otp:
                    user.otp = None
                    user.password_change = True
                    user.otp_attempt = 0
                    user.save(update_fields=["otp", "password_change", "otp_attempt"])
                    return attrs
                else:
                    if user.otp_attempt<2:
                            user.otp_attempt = user.otp_attempt+1
                            user.save(update_fields=["otp_attempt"])
                            error_obj = {"otp": "Wrong OTP."}
                    else:
                        user.otp = None
                        user.otp_attempt = 0
                        user.save(update_fields=["otp", "otp_attempt"])
                        error_obj = {"otp": "Expired, resend OTP"}
                    raise serializers.ValidationError({"otp": "Wrong OTP."})
        except IntegrityError as e:
            raise serializers.ValidationError({"message": str(e)})
        raise serializers.ValidationError(error_obj)
# =====================================================================        
class ForgetPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
    def validate(self, attrs):
        number = attrs.get('phone_number')
        new_password = attrs.get('new_password')
        user = User.objects.filter(phone_number = number).only("uuid").first()
        if user is None:
            raise serializers.ValidationError({"phone_number": "No user is registered against this number."}, code="frontend")
        
        if not user.password_change:
            raise res.Forbidden()

        try:
            validate_password(new_password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"new_password": serializer_error["non_field_errors"]})
            
        user.set_password(new_password)
        user.password_change = False
        user.save(update_fields=["password", "password_change"])
        return attrs
    
    
