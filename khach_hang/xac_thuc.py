"""Xác thực bằng email cho cửa hàng và trang quản trị."""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, *, email=None, **kwargs):
        # Django Admin gửi email qua tham số username của AuthenticationForm.
        email = (email if email is not None else username or "").strip()
        if not email or password is None or len(email) > 254:
            return None

        try:
            user = User.objects.get(email__iexact=email)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
