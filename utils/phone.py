# from rest_framework.response import Response
from utils.response import success_created
from utils.response import ServerError
from rest_framework import serializers
from rest_framework import status
from django.conf import settings

###################################################################
                            # Helping Functions
###################################################################



def send_phone_message(message, number):
    # Use the configuration for sending the message
    print("Message sent to: ", number)
    responseData = {"messages": [{"status": "0"}]}
    return responseData


# ==============================================================


# This is the function to send the OTP. This will be in user after configuring the Vonage
def send_otp(serialize):
    try:
        otp = serialize.validated_data.get('otp')
        data = serialize.data
        user_num = "+92"+str(serialize.validated_data.get('phone_number'))
        message = "Your otp verfication code is \n" + str(otp)
        res = send_phone_message(number=user_num, message=message)
        data['otp_status'] = "OTP send."
        if res["messages"][0]["status"] != "0":
            data['otp_status'] = "OTP does not send."
        return data
    except Exception as e:
        raise ServerError({"message": str(e)})

