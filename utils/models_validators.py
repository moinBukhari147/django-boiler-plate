from datetime import date
from django.core.exceptions import ValidationError

def AgeValidator(value):
    todayy = date.today()
    age = todayy.year - value.year -  ((todayy.month, todayy.day)< (value.month, value.day))
    if age<18:
        raise ValidationError ("You are under age.")
def GenderValidator(value):
    if value.lower() not in ["male", "female"]:
        raise ValidationError("The selected option does not exists.")
    
def ValueValidator(value,menu, partner = False):
    # first check if value is emptpy don't raise error we have set balnk=True if value not empty and not in list and partner = false raise error and if value is not empty and not in list and is not "does not maater" raise error the selected option does not exist.
    if value!="none" and value.lower() not in menu:
        if not partner or (partner and value.lower() !="does not matter"):
            raise ValidationError("The selected option does not exist.")
    
def ValueValidatorWithoutNone(value,menu, partner = False):
    if value.lower() not in menu:
        if not partner or (partner and value.lower() !="does not matter"):
            raise ValidationError("The selected option does not exist.")
        
