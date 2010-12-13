from django.forms import ModelForm
from autoentrepreneur.models import UserProfile

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user', 'address']

