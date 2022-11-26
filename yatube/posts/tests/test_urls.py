from http import HTTPStatus

from django.urls import reverse
from django.test import Client, TestCase
from posts.models import Group, Post
from core.models import User
from django.core.cache import cache


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        cache.clear()

    def test_page_guest_client(self):
        """Страницы доступны по URL"""
        url_names_status_code = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK
        }
        for address, status_code in url_names_status_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_post_create_url_redirect_anonymous_on_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            reverse('posts:post_create'), follow=True
        )
        self.assertRedirects(
            response, (reverse('auth:login') + '?next=' + '/create/'))

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """Страница по адресу /posts/<int:post_id>/edit/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, (
                reverse(
                    'auth:login'
                ) + '?next=' + '/posts/' + str(self.post.pk) + '/edit/'
            )
        )

    def test_non_existent_url(self):
        """Страница по несуществующему адресу не доступна"""
        response = self.guest_client.get('posts/home/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_url_uses_correct_template(self):
        """Проверка шаблонов для неавторизованного пользователя."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_url_uses_correct_template_authorized_client(self):
        """Проверка шаблона create_post.html
        для авторизованного пользователя."""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_url_uses_correct_template_author(self):
        """Проверка шаблона create_post.html для автора."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')
