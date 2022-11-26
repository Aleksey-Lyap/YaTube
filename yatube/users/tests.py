from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_password_exists_at_desired_location(self):
        """Проверка доступности адреса /auth/password_reset/."""
        response = self.guest_client.get('/auth/password_reset/')
        self.assertEqual(response.status_code, 200)

    def test_url_exists_at_desired_location(self):
        """Проверка доступности адресов."""
        url_names_status_code = {
            '/auth/login/': 200,
            '/auth/logout/': 200,
            '/auth/signup/': 200
        }
        for address, status_code in url_names_status_code.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_users_url_uses_correct_template(self):
        """Проверка шаблона для адресов users."""
        templates_url_names = {
            'users/logged_out.html': '/auth/logout/',
            'users/login.html': '/auth/login/',
            'users/signup.html': '/auth/signup/'
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
