import shutil
import tempfile

from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from posts.models import Group, Post, Comment, Follow
from core.models import User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewsTests(TestCase):
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
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostViewsTests.user)

    def setUp(self):
        cache.clear()

    def test_post_views_uses_correct_template(self):
        """Проверка шаблонов по namespace:name."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание'
        )
        bilk_post: list = []
        for i in range(1, 14):
            bilk_post.append(Post(text=f'Тестовый текст {i}',
                                  group=cls.group,
                                  author=cls.user))
        Post.objects.bulk_create(bilk_post)

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_page_1_paginator_guest_client(self):
        '''Проверка количества постов на первой страницы. '''
        pages = {
            reverse('posts:index'): 10,
            reverse(
                'posts:profile', kwargs={'username': f'{self.user}'}
            ): 10,
            reverse(
                'posts:group_list', kwargs={'slug': f'{self.group.slug}'}
            ): 10,
        }
        for page, count in pages.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertIsInstance(
                    response.context['page_obj'].paginator, Paginator
                )
                self.assertEqual(len(response.context['page_obj']), count)

    def test_page_2_paginator_guest_client(self):
        '''Проверка количества постов на второй страницы. '''
        pages = {
            reverse('posts:index'): 3,
            reverse(
                'posts:profile', kwargs={'username': f'{self.user}'}
            ): 3,
            reverse(
                'posts:group_list', kwargs={'slug': f'{self.group.slug}'}
            ): 3,
        }
        for page, count in pages.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page + '?page=2')
                self.assertIsInstance(
                    response.context['page_obj'].paginator, Paginator
                )
                self.assertEqual(len(response.context['page_obj']), count)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Коммент',
            author=cls.user
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def same_obj(self, obj):
        self.assertEqual(obj.pub_date, self.post.pub_date)
        self.assertEqual(obj.author, self.user)
        self.assertEqual(obj.text, self.post.text)
        self.assertEqual(obj.group, self.group)
        self.assertIn(self.uploaded.name, obj.image.name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertGreater(len(response.context['page_obj']), 0)
        self.assertIsInstance(
            response.context['page_obj'].paginator, Paginator
        )
        object = response.context['page_obj'][0]
        self.same_obj(object)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertIn('page_obj', response.context)
        self.assertGreater(len(response.context['page_obj']), 0)
        self.assertIsInstance(
            response.context['page_obj'].paginator, Paginator
        )
        object = response.context['page_obj'][0]
        object2 = response.context['group']
        self.same_obj(object)
        self.assertEqual(object2, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertIn('page_obj', response.context)
        self.assertGreater(len(response.context['page_obj']), 0)
        self.assertIsInstance(
            response.context['page_obj'].paginator, Paginator
        )
        object = response.context['page_obj'][0]
        object2 = response.context['author']
        self.same_obj(object)
        self.assertEqual(object2, self.user)
        following_object = response.context['following']
        self.assertEqual(following_object, False)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        object = response.context['post']
        object2 = response.context['comments']
        self.same_obj(object)
        self.assertIn(self.comment, object2)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
            object = response.context['post']
            self.assertEqual(object.text, self.post.text)
            self.assertEqual(object.group.title, self.group.title)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Тестовый текст',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.user_follow = User.objects.create(username='follow')
        cls.user_unfollow = User.objects.create(username='unfollow')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            image=None,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client_follow = Client()
        self.authorized_client_follow.force_login(FollowTest.user_follow)
        self.authorized_client_unfollow = Client()
        self.authorized_client_unfollow.force_login(FollowTest.user_unfollow)
        cache.clear()

    def test_user_follow_author(self):
        self.assertFalse(
            Follow.objects.filter(user=self.user_follow, author=self.author)
        )
        self.authorized_client_follow.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user_follow, author=self.author)
        )

    def test_user_unfollow_author(self):
        Follow.objects.create(user=self.user_unfollow, author=self.author)
        self.authorized_client_unfollow.get(
            reverse(
                'posts:profile_unfollow', kwargs={'username': self.author}
            )
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user_unfollow, author=self.author)
        )

    def test_follow_appear_post(self):
        self.authorized_client_follow.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.post = Post.objects.create(
            author=self.author,
            text='text',
        )
        response = self.authorized_client_follow.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.post, response.context['page_obj'])

    def test_unfollow_not_appear_post(self):
        self.authorized_client_unfollow.get(
            reverse(
                'posts:profile_unfollow', kwargs={'username': self.author}
            )
        )
        self.post = Post.objects.create(
            author=self.author,
            text='text2323',
        )
        response = self.authorized_client_unfollow.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(self.post, response.context['page_obj'])
