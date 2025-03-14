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
from rest_framework_simplejwt.tokens import RefreshToken
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
            raise serializers.ValidationError({"message":"Choose a strong passowrd of min 8 characters.", })
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
    
    # Customize the update method to update the user as per the requirement
    # def update(self, instance, validated_data):
    #     return super().update(instance, validated_data)


# =====================================================================
# This serializer is used for both
# OTP verification of the newly creted user phone number
# OTP verification of the user phone number change
class VerifyOtpSerialzer(serializers.Serializer):
    otp = serializers.IntegerField(min_value = 100010,max_value =999989)
    phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
    
    def validate(self, attrs):
        try:
            with transaction.atomic():
                number = attrs.get('phone_number')
                otp = attrs.get('otp')
                # select_for_update is used to lock the row until the transaction is completed
                user = User.objects.select_for_update().filter(new_number = number).only("phone_number", "new_number", "otp", "otp_attempt", "is_active").first()
                
                if user is None:
                    raise serializers.ValidationError(
                        {"phone_number": "Number not registered or no OTP send to this number."}, code="frontend")
                if not user.new_number:
                    raise res.ConflictError({"message": "Number is already verified."})
                
                if not user.otp:
                    raise serializers.ValidationError({"message": "OTP is not send to this number. Generate OTP first."})

                if not user.otp ==otp:
                    user.otp_attempt = user.otp_attempt+1
                    if user.otp_attempt>2:
                        user.otp = None
                        user.otp_attempt = 0
                        user.save(update_fields=["otp", "otp_attempt"])
                        raise serializers.ValidationError({"otp": "Expired, resend OTP"})
                    else:
                        user.save(update_fields=["otp_attempt"])
                        raise serializers.ValidationError({"otp": "Wrong OTP."})
                
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
        except IntegrityError as e:
            raise serializers.ValidationError({"message": str(e)})
        
# # =====================================================================
# class ResendOtpSerializer(serializers.Serializer):
#     phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
#     def validate(self, attrs):
#         number = attrs.get('phone_number')
#         user = User.objects.filter(new_number= number).first()
#         if not user:
#             raise serializers.ValidationError({"Error request cannot be proceed."})
#         otp = random.randint(100010, 999989)
#         user.otp = otp
#         user.save()
#         attrs['otp'] = otp
#         return attrs
    
# # =====================================================================
# class ChangeNumberSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["phone_number"]
#     def validate(self, attrs):
#         user = self.context.get('user')
#         if attrs.get("phone_number") == user.phone_number:
#             raise serializers.ValidationError({"phone_number": "This number is already registered with your profile."})
#         otp = random.randint(100010, 999989)
#         attrs['otp']= otp
#         return attrs

#     def update(self, instance, validated_data):
#         instance.new_number = validated_data.get('phone_number', instance.new_number)
#         instance.otp = validated_data.get('otp')
#         instance.save()
#         return instance

# class ForgetPasswordSerializer(serializers.Serializer):
#     phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
#     def validate(self, attrs):
#         number = attrs.get('phone_number')
#         user = User.objects.filter(phone_number= number).first()
#         if not user:
#             raise serializers.ValidationError({"phone_number": "This number is not regiestered against any user."})
#         otp = random.randint(100010, 999989)
#         user.otp = otp
#         user.save()
#         return attrs
    
# # =====================================================================
# class ForgetPasswordOtpVerifySerializer(serializers.Serializer):
#     phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
#     otp = serializers.IntegerField(min_value = 100010,max_value =999989)
    
#     def validate(self, attrs):
#         number = attrs.get('phone_number')
#         otp = attrs.get('otp')
#         user = User.objects.filter(phone_number = number).first()
        
#         if not(user and user.otp):
#             raise serializers.ValidationError(
#                 {"error_cannot_proceed":"Again enter number and then verify OTP."})
        
#         if user.otp ==otp:
#             user.otp = None
#             user.password_change = True
#             user.otp_attempt = 0
#             user.save()
#             return attrs
#         else:
#             user.otp_attempt = user.otp_attempt+1
#             if user.otp_attempt>2:
#                 user.otp = None
#                 user.otp_attempt = 0
#                 user.save()
#                 raise serializers.ValidationError({"otp": "Expired, resend OTP"})
#             user.save()
#             raise serializers.ValidationError({"otp": "Wrong OTP."})
        
# # =====================================================================        
# class ForgetPasswordResetSerializer(serializers.Serializer):
#     new_password = serializers.CharField(style={"input_type": "password"}, write_only=True)
#     phone_number = serializers.IntegerField(min_value = 3000000000, max_value=3499999999)
#     def validate(self, attrs):
#         number = attrs.get('phone_number')
#         user = User.objects.filter(phone_number = number).first()
#         # if the user is None then someone is trying to break the API, or there is an implementation error.
#         if user is None:
#             raise serializers.ValidationError("Error cannot proceed.")
        
#         # if password_change = True this means user can change his password now
#         if not user.password_change:
#             raise serializers.ValidationError({"cannot_reset_password.":"First goto forget password, provide your number and verify otp to change password."})
        
#         # is_same_password = user.check_password(raw_password=attrs['new_password'])
#         # if is_same_password:
#         #     raise serializers.ValidationError({"new_password": "Error, password is same as previous. Try new one"})
        
#         try:
#             validate_password(attrs['new_password'], user)
#         except django_exceptions.ValidationError as e:
#             serializer_error = serializers.as_serializer_error(e)
#             raise serializers.ValidationError(
#                 {"new_password": serializer_error["non_field_errors"]})
            
#         user.set_password(attrs['new_password'])
#         user.password_change = False
#         user.save()
#         return super().validate(attrs)
    
# # =====================================================================  
# class AddEmailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ("email",)
#         extra_kwargs = {
#             "email": {"required": True}
#         }
#     def update(self, instance, validated_data):
#         instance.email = validated_data.get('email', instance.email)
#         instance.save()
#         return super().update(instance, validated_data)
# # =====================================================================  
# class LogoutSerialzier(serializers.Serializer):
#     token = serializers.CharField()
#     def validate(self, attrs):
#         token = attrs.get('token')
#         try:
#             refresh_token = RefreshToken(token=token)
#             refresh_token.blacklist()
#         except Exception as e:
#             raise serializers.ValidationError({"token": "Invalid token"})
#         return attrs
    
    
# # =================== Profile model serializers ===============================

# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = m.Profile
#         exclude = ('blur_img',)
#         extra_kwargs = {"user": {"read_only": True}}
    
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 profile = m.Profile.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one profile.",
#                 "front_error": error})
#         return profile

# class ProfileUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = m.Profile
#         fields = ('degree', 'earning', 'blur_img', 'marital_status')
    
# # ========================= About me Serializer ===========================

# # From here to below the create method is only called when there is an issue in the signal due to which the table is not created so the bakup post method will call and create metod handle that backup post request.
# class AboutmeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Aboutme
#         exclude = ["user"]
#     def validate_father_name(self, value):
#         if value == "none":
#             raise serializers.ValidationError({value: "value cannot be none."})
#         return value
#     def validate_my_personality(self, value):
#         if value == "none":
#             raise serializers.ValidationError({value: "value cannot be none."})
#         return value
#     def validate_p_personality(self, value):
#         if value == "none":
#             raise serializers.ValidationError({value: "value cannot be none."})
#         return value
#     def validate_sub_cast(self, value):
#         if value == "none":
#             raise serializers.ValidationError({value: "value cannot be none."})
#         return value
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 aboutme = Aboutme.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one about me section.",
#                 "front_error": error})
#         return aboutme

# class AboutmeUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Aboutme
#         fields = ["my_personality", "p_personality", "wives", "children"]
        

# # =================== AddressContact model serializers =====================


# class AddressContactSerializer(serializers.ModelSerializer):
#     user_number = serializers.ReadOnlyField()
#     class Meta:
#         model = AddressContact
#         exclude = ["user"]
        
#     def validate_guardian_number(self, value):
#         if value == self.context['user_num']:
#             raise serializers.ValidationError("Gaurdian number cannot be same as user number.")
#         return value
#     def validate_address(self, value):
#         if value == "none":
#             raise serializers.ValidationError({value: "value cannot be none."})
#         return value
#     def validate_other_nationality(self, value):
#         if value == "none":
#             raise serializers.ValidationError({value: "value cannot be none."})
#         return value
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 profile = AddressContact.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one address contact section.",
#                 "front_error": error})
#         return profile

# # =====================================================================        

# class MeetingContactSerializer(serializers.ModelSerializer):
#     name = serializers.ReadOnlyField(source="user_name")
#     phone_number = serializers.IntegerField(source="user_number")
#     city = serializers.ReadOnlyField(source="user_city")
#     guardian_name = serializers.ReadOnlyField(source="user_guardian_name")
    
#     class Meta:
#         model = AddressContact
#         fields = [ "name","phone_number","guardian_name", "guardian_number",  "city", "address"]
    
    
# # =================== Looks model serializers =====================
    
# class LooksSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Looks
#         exclude = ["user"]
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 profile = Looks.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one Looks section.",
#                 "front_error": error})
#         return profile
    
# # =================== Education model serializers =====================

# class EducationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Education
#         exclude = ["user"]
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 education = Education.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one Education section.",
#                 "front_error": error})
#         return education

# class EducationUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Education
#         fields = ["degree_major"]

# # =================== Family model serializers =====================

# class FamilySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Family
#         exclude = ["user"]
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 family = Family.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one Family section.",
#                 "front_error": error})
#         return family

# class FamilyUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Family
#         fields = ["house", "house_size", "house_stories"]
# # =================== Profession model serializers =====================

# class ProfessionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profession
#         exclude = ["user"]
#     def validate_job_title(self, value):
#         if value == "none":
#             raise serializers.ValidationError({value: "value cannot be none."})
#         return value
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 profession = Profession.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one Profession section.",
#                 "front_error": error})
#         return profession
    
    
# # =================== ReligionPractice model serializers =====================

# class ReligionPracticeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReligionPractice
#         exclude = ["user"]
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 reg = ReligionPractice.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one Religion section.",
#                 "front_error": error})
#         return reg


# # =================== Personality model serializers =====================

# class PersonalitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Personality
#         exclude = ["user"]
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 personality = Personality.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one Personality section.",
#                 "front_error": error})
#         return personality


# # =================== Image Serializers serializers =====================
# # On client side add or delete the image one by one
# # wrote the custom logic for delete method and make the image none
# # wrote the custom logic for change profile pic.
# class ImagesSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Images
#         exclude = ("user",)
        
#     def is_same_img(self, value,profile_img, img_1, img_2, img_3, img_4):
#         value_webp = str(value).split(".")[0] + ".webp"
#         if value_webp in [profile_img, img_1, img_2, img_3, img_4]:
#             raise serializers.ValidationError({"error": "Image is already uploaded."})
#     def compressed_img(self,img):
#         image_name = str(img).split(".")[0]
#         image = Image.open(img)
#         image_io = io.BytesIO()
#         image.save(image_io, 'webp')
#         image_io.seek(0)
#         image_webp = InMemoryUploadedFile(image_io, None,
#                                         image_name+'.webp',
#                                         'image/webp',
#                                         image_io.tell(),
#                                         None)
#         return image_webp
#     def remove_previous_img(self, num, img_name):
#         img_path = os.path.join(settings.MEDIA_ROOT, "images",str(num), img_name)
#         if os.path.exists(img_path):
#             os.remove(img_path)
        
#     def validate(self, attrs):
#         user = self.context.get("user")
#         method = self.context.get("method")
#         if method =="PATCH":
#             # getting all the images name of user to check the duplication of the comming image
#             profile_img = str(user.images.profile_pic).split("/")[-1]
#             img_1 = str(user.images.pic_1).split("/")[-1]
#             img_2 = str(user.images.pic_2).split("/")[-1]
#             img_3 = str(user.images.pic_3).split("/")[-1]
#             img_4 = str(user.images.pic_4).split("/")[-1]
#             num = user.phone_number
#             # ------------------------------------------------------------------
#             profile_pic = attrs.get("profile_pic", None)
#             if profile_pic is not None:
#                 self.is_same_img(str(profile_pic), profile_img, img_1, img_2, img_3, img_4)
#                 attrs['profile_pic'] = self.compressed_img(profile_pic)
#                 if profile_img:
#                     self.remove_previous_img(num=num, img_name=profile_img)

#             # ------------------------------------------------------------------
#             pic_1 = attrs.get("pic_1", None)
#             if pic_1 is not None:
#                 self.is_same_img(str(pic_1), profile_img,img_1, img_2, img_3, img_4)
#                 attrs['pic_1'] = self.compressed_img(pic_1)
#                 if img_1:
#                     self.remove_previous_img(num=num, img_name=img_1)

#             # ------------------------------------------------------------------
#             pic_2 = attrs.get("pic_2", None)
#             if pic_2 is not None:
#                 self.is_same_img(str(pic_2), profile_img, img_1,img_2, img_3, img_4)
#                 attrs['pic_2'] = self.compressed_img(pic_2)
#                 if img_2:
#                     self.remove_previous_img(num=num, img_name=img_2)

#             # ------------------------------------------------------------------
#             pic_3 = attrs.get("pic_3", None)
#             if pic_3 is not None:
#                 self.is_same_img(str(pic_3), profile_img, img_1, img_2,img_3, img_4)
#                 attrs['pic_3'] = self.compressed_img(pic_3)
#                 if img_3:
#                     self.remove_previous_img(num=num, img_name=img_3)

#             # ------------------------------------------------------------------
#             pic_4 = attrs.get("pic_4", None)
#             if pic_4 is not None:
#                 self.is_same_img(str(pic_4), profile_img, img_1, img_2, img_3, img_4)
#                 attrs['pic_4'] = self.compressed_img(pic_4)
#                 if img_4:
#                     self.remove_previous_img(num=num, img_name=img_4)
#         return attrs
    
#     def create(self, validated_data):
#         try:
#             with transaction.atomic():
#                 images = Images.objects.create(**validated_data)
#         except IntegrityError as e:
#             error = str(e)
#             raise serializers.ValidationError({"integrity_error": "One user can only have one Images section.",
#                 "front_error": error})
#         return images

# # =====================================================================        
# class DeleteImageSerializer(serializers.ModelSerializer):
#     image_field = serializers.CharField(max_length = 11)
#     class Meta:
#         model = Images
#         fields = ("image_field",)
#     # delte the image from the storeage    
#     def delete_image(self, img_path, img_field):
#         if os.path.exists(img_path):
#             try:
#                 os.remove(img_path)
#             except Exception as e:
#                 error = str(e)
#                 raise serializers.ValidationError({
#                     img_field: "image cannot be deleted.",
#                     "front_error": error})
#     def validate(self, attrs):
#         image_field = attrs.get("image_field")
#         user = self.context.get('user')
#         if image_field not in menu.image_field_name:
#             raise serializers.ValidationError({"image_field": "This field does not belong to any image field."})
#         if image_field == "profile_pic":
#             raise serializers.ValidationError({"profile_pic": "profile pic cannot be deleted. It can only be changed."})
#         # ------------------------------------------------------
#         if image_field == "pic_1":
#             if not user.images.pic_1:
#                 raise serializers.ValidationError({"pic_1": "image is already deleted."})
#             img_path = os.path.join(settings.MEDIA_ROOT, str(user.images.pic_1))
#             self.delete_image(img_path=img_path, img_field=image_field)
            
#             # setting image in database to none
#             user.images.pic_1 = None
#             user.images.save()
            
#         # -----------------------------------------------------------   
#         elif image_field == "pic_2":
#             if not user.images.pic_2:
#                 raise serializers.ValidationError({"pic_2": "image is already deleted."})
#             img_path = os.path.join(settings.MEDIA_ROOT, str(user.images.pic_2))
#             self.delete_image(img_path=img_path, img_field=image_field)
#             # setting image in database to none
#             user.images.pic_2 = None
#             user.images.save()
            
#         # -----------------------------------------------------------   
#         elif image_field == "pic_3":
#             if not user.images.pic_3:
#                 raise serializers.ValidationError({"pic_3": "image is already deleted."})
#             img_path = os.path.join(settings.MEDIA_ROOT, str(user.images.pic_3))
#             self.delete_image(img_path=img_path, img_field=image_field)
#             # setting image in database to none
#             user.images.pic_3 = None
#             user.images.save()
            
#         # -----------------------------------------------------------
#         elif image_field == "pic_4":
#             if not user.images.pic_4:
#                 raise serializers.ValidationError({"pic_4": "image is already deleted."})
#             img_path = os.path.join(settings.MEDIA_ROOT, str(user.images.pic_4))
#             self.delete_image(img_path=img_path, img_field=image_field)

#             # setting image in database to none
#             user.images.pic_4 = None
#             user.images.save()
#         return super().validate(attrs)
# # =====================================================================
# class MakeProfilePicSerializer(DeleteImageSerializer):
#     def validate(self, attrs):
#         image_field = attrs.get("image_field")
#         user = self.context.get('user')
#         if image_field not in menu.image_field_name:
#             raise serializers.ValidationError({"image_field": "This field does not belong to any image field."})
#         if image_field == "profile_pic":
#             raise res.ValidationAccept({"detail": "This is already a profile pic."}, code="accepted")
#         # ------------------------------------------------------
#         if image_field == "pic_1":
#             if not user.images.pic_1:
#                 raise serializers.ValidationError({image_field: "There is no image. Image none"})
#             user.images.profile_pic, user.images.pic_1 = user.images.pic_1, user.images.profile_pic
#             user.images.save()
#         # ------------------------------------------------------
#         if image_field == "pic_2":
#             if not user.images.pic_2:
#                 raise serializers.ValidationError({image_field: "There is no image. Image none"})
#             user.images.profile_pic, user.images.pic_2 = user.images.pic_2, user.images.profile_pic
#             user.images.save()
#         # ------------------------------------------------------
#         if image_field == "pic_3":
#             if not user.images.pic_3:
#                 raise serializers.ValidationError({image_field: "There is no image. Image none"})
#             user.images.profile_pic, user.images.pic_3 = user.images.pic_3, user.images.profile_pic
#             user.images.save()
#         # ------------------------------------------------------
#         if image_field == "pic_4":
#             if not user.images.pic_4:
#                 raise serializers.ValidationError({image_field: "There is no image. Image none"})
#             user.images.profile_pic, user.images.pic_4 = user.images.pic_4, user.images.profile_pic
#             user.images.save()
#         return attrs


# # =====================================================================

# # This serializer is dedicated to get all only those fileds that can be updated after the profile verification.
# # This serializer get those all fields in the single request.
# # The patch request for those tables are already designed.
# class GetUpdateFieldsSerializer(serializers.ModelSerializer):
#     profile = ProfileUpdateSerializer()
#     aboutme = AboutmeUpdateSerializer()
#     education = EducationUpdateSerializer()
#     family = FamilyUpdateSerializer()
#     address_contact = AddressContactSerializer()
#     class Meta:
#         model = User
#         fields = ["profile", "aboutme", "education", "family", "address_contact"]