from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from utils.permission import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from . import models as m
from rest_framework.response import Response
from utils.response import ServerError
from utils.response import success_created, success_ok
from rest_framework import status
from utils.phone import send_otp
from . import serializers as ser
from rest_framework_simplejwt.tokens import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenBlacklistSerializer
from rest_framework.serializers import ValidationError



###################################################################
                            # Views
###################################################################

class UserViewSet(ModelViewSet):
    User = get_user_model()
    queryset = User.objects.none()
    def get_serializer_class(self):
        if self.action == "signup":
            return ser.UserCreateSerializer
        elif self.action == "me":
            return ser.UpdateUserSerializer
        elif self.action == "otp_verify":
            return ser.VerifyOtpSerialzer
        elif self.action == "otp_resend":
            return ser.ResendOtpSerializer
        elif self.action == "number_change":
            return ser.ChangeNumberSerializer
        elif self.action == "login":
            return TokenObtainPairSerializer
        elif self.action =="forget_password":
            return ser.ForgetPasswordSerializer
        elif self.action == "forget_password_otp_verify":
            return ser.ForgetPasswordOtpVerifySerializer
        elif self.action == "forget_password_reset":
            return ser.ForgetPasswordResetSerializer
        elif self.action == "logout":
            return TokenBlacklistSerializer
    

    
    def get_permissions(self):
        if self.action in ["number_change","add_email","me", "logout"]:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    
    
    # ===================================
                    # ACTIONS
    # ===================================

    @action(["post"], detail=False)
    def test(self, request, *args, **kwargs):
        return Response({"ok": "it's running. "}, status=status.HTTP_200_OK)

# -----------------------------------------------------------
    @action(["post"], detail=False)
    def signup(self, request,*args, **kwargs):
        try:
            serializer = self.get_serializer(data = request.data)
            if serializer.is_valid(raise_exception = True):
                serializer.save()
            data = send_otp(serializer)
            return success_created("User created and Otp send successfully.",data)
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})
# -----------------------------------------------------------
    @action(["post"], detail=False, url_path="otp-verify")
    def otp_verify(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data= request.data)
            serializer.is_valid(raise_exception = True)
            if "tokens" in serializer.validated_data:
                token = serializer.validated_data.get("tokens")
                return success_created("OTP verified successfully.", token)
            return success_created("OTP verified successfully.")
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})
# -----------------------------------------------------------
    @action(['post'], detail= False, url_path="otp-resend")
    def otp_resend(self, request):
        try:
            serializer = self.get_serializer(data = request.data)
            serializer.is_valid(raise_exception = True)
            send_otp(serializer)
            return success_created("Otp resend successfully")
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})
# -----------------------------------------------------------
    @action(["post"], detail=False)
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data= request.data)
        serializer.is_valid(raise_exception = True)
        return success_ok("User logged in successfully.", serializer.validated_data)
# -----------------------------------------------------------
    @action(["get", "patch"], detail=False)
    def me(self, request, *args, **kwargs):
        if request.method == "GET":
            instance = request.user
            serializer = self.get_serializer(instance)
            return success_ok("User details fetched successfully.", serializer.data)
        if request.method == "PATCH":
            instance = request.user
            context = {"user": request.user}
            serializer = self.get_serializer(instance, data = request.data, context = context, partial = True)
            serializer.is_valid(raise_exception = True)
            serializer.save()
            return success_ok("User details updated successfully.", serializer.data)
        
# -----------------------------------------------------------
    @action(['patch'], detail= False, url_path="number-change")
    def number_change(self, request):
        try:
            instance = request.user
            context = {"user": request.user}
            serializer = self.get_serializer(instance,data = request.data, context = context )
            serializer.is_valid(raise_exception = True)
            serializer.save()
            send_otp(serializer)
            return success_ok("Otp send successfully to new number.")
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})
# -----------------------------------------------------------
    @action(['post'], detail= False, url_path="forget-password")
    def forget_password(self, request):
        try:
            serializer = self.get_serializer(data = request.data)
            serializer.is_valid(raise_exception = True)
            send_otp(serializer)
            return success_ok("Otp send to your number, veirfy opt and reset password.")
        except Exception as e:
            print(e)
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})

# -----------------------------------------------------------
    @action(['post'], detail= False, url_path="forget-password-otp-verify")
    def forget_password_otp_verify(self, request):
        try: 
            serializer = self.get_serializer(data = request.data)
            serializer.is_valid(raise_exception = True)
            return success_ok("Otp verified successfully. You can reset password now.")
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})
# -----------------------------------------------------------
    @action(['post'], detail= False, url_path="password-reset")
    def forget_password_reset(self, request):
        try:
            serializer = self.get_serializer(data = request.data)
            serializer.is_valid(raise_exception = True)
            return success_ok("Password reset successfully.")
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})

# -----------------------------------------------------------
    @action(['post'], detail= False)
    def logout(self, request):
        try:
            serializer = self.get_serializer( data = request.data)
            serializer.is_valid(raise_exception = True)
            return success_ok("User logged out successfully.")
        except TokenError as e:
            raise ValidationError({"message": str(e)})
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})