from rest_framework.exceptions import APIException
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ModelViewSet
from . import models as m
from rest_framework.response import Response
from utils.response import ServerError
from django.shortcuts import render
from utils.phone import send_otp
from rest_framework import status
from . import serializers as ser



###################################################################
                            # Views
###################################################################

class UserViewSet(ModelViewSet):
    User = get_user_model()
    queryset = User.objects.all()
    def get_serializer_class(self):
        if self.action == "signup" or self.action == "me":
            return ser.UserCreateSerializer
        elif self.action == "otp_verify":
            return ser.VerifyOtpSerialzer
        # elif self.action == "resend_otp":
        #     return ResendOtpSerializer
        # elif self.action == "change_number":
        #     return ChangeNumberSerializer
        # elif self.action =="forget_password":
        #     return ForgetPasswordSerializer
        # elif self.action == "forget_password_otp_verify":
        #     return ForgetPasswordOtpVerifySerializer
        # elif self.action == "forget_password_reset":
        #     return ForgetPasswordResetSerializer
        # elif self.action == "add_email":
        #     return AddEmailSerializer
        # elif self.action == "logout":
        #     return LogoutSerialzier
    

    
    def get_permissions(self):
        if self.action in ["change_number","add_email","me", "logout"]:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    
    
    # ===================================
                    # ACTIONS
    # ===================================

    @action(["post"], detail=False)
    def test(self, request, *args, **kwargs):
        return Response({"ok": "it's running. "}, status=status.HTTP_200_OK)
    
# -----------------------------------------------------------
    @action(["get"], detail=False)
    def me(self, request, *args, **kwargs):
        instance = request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
# -----------------------------------------------------------
    @action(["post"], detail=False)
    def signup(self, request,*args, **kwargs):
        try:
            serializer = self.get_serializer(data = request.data)
            if serializer.is_valid(raise_exception = True):
                serializer.save()
            return send_otp(serializer)
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})
# -----------------------------------------------------------
    @action(["post"], detail=False, url_path="opt-verify")
    def otp_verify(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data= request.data)
            serializer.is_valid(raise_exception = True)
            if "tokens" in serializer.validated_data:
                return Response(serializer.validated_data.get("tokens"), status=status.HTTP_202_ACCEPTED)
            return Response({"success": "OTP verified."},status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            raise e if isinstance(e, APIException) else ServerError({"message": str(e)})
    @action(['post'], detail= False)
    def resend_otp(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        # This statement will be used after configuring the Vonage for sending the OTP.
        # return self.send_otp(serializer)
        res = {"otp": "Otp resend successfully."}
        return Response(res, status=status.HTTP_200_OK)
    
    @action(['patch'], detail= False)
    def change_number(self, request):
        context = {"user": request.user}
        serializer = self.get_serializer( request.user ,data = request.data, context = context,partial=True )
        serializer.is_valid(raise_exception = True)
        serializer.save()
        # This statement will be used after configuring the Vonage for sending the OTP.
        # return self.send_otp(serializer)
        return Response("Otp send Successfully", status=status.HTTP_200_OK)

    @action(['post'], detail= False)
    def forget_password(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        # This statement will be used after configuring the Vonage for sending the OTP.
        # return self.send_otp(serializer)
        res = {"otp": "Otp send successfully."}
        return Response(res, status=status.HTTP_200_OK)

    @action(['post'], detail= False)
    def forget_password_otp_verify(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        res = {"otp": "Otp verified, you can change password."}
        return Response(res, status=status.HTTP_200_OK)

    @action(['post'], detail= False)
    def forget_password_reset(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        res = {"success": "Password changed sucessfully."}
        return Response(res, status=status.HTTP_200_OK)
    
    @action(['patch'], detail= False)
    def add_email(self, request):
        serializer = self.get_serializer( request.user ,data = request.data, partial=True )
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    @action(['post'], detail= False)
    def logout(self, request):
        serializer = self.get_serializer( data = request.data)
        serializer.is_valid(raise_exception = True)
        return Response("logut successfull", status=status.HTTP_200_OK)