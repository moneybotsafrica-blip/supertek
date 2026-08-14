from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with either
    their username or email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find a user matching either username or email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # No user with this username/email was found
            return None
        except User.MultipleObjectsReturned:
            # This could happen if you allow duplicate emails and someone uses an email as username
            # In this case we return the first match
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).first()
            if user.check_password(password):
                return user
            
        return None 