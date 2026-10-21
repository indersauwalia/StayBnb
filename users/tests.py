from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Profile


class AccountFlowTests(TestCase):
    def test_signup_creates_account_and_role_profile(self):
        response = self.client.post(reverse("users:signup"), {
            "first_name": "Riya",
            "username": "riya",
            "email": "riya@example.com",
            "role": Profile.HOST,
            "password1": "A-long-safe-passphrase-93",
            "password2": "A-long-safe-passphrase-93",
        })

        self.assertRedirects(response, reverse("users:dashboard"))
        user = User.objects.get(username="riya")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertEqual(Profile.objects.get(user__username="riya").role, Profile.HOST)

    def test_dashboard_redirects_anonymous_visitors_to_login(self):
        response = self.client.get(reverse("users:dashboard"))

        self.assertRedirects(response, f"{reverse('users:login')}?next={reverse('users:dashboard')}")
