# from rest_framework.response import Response
from utils.response import success_created
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
        user_num = "+92"+str(serialize.validated_data.get('phone_number'))
        message = "Your otp verfication code is \n" + str(otp)
        res = send_phone_message(number=user_num, message=message)
        Status = "OTP send."
        if res["messages"][0]["status"] != "0":
            Status = "OTP does not send."
        data = serialize.data
        data['OTP status']= Status
        return success_created(message="OTP send successfully.", data=data)
    except Exception as e:
        Status = "Exception is raised while sending the OTP."