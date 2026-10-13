from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Post


class DraftVisibilityTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user('author', password='pw')
        cls.other = User.objects.create_user('other', password='pw')
        cls.admin = User.objects.create_superuser('admin', password='pw')
        cls.draft = Post.objects.create(author=cls.author, title='Secret draft', text='draft body')
        cls.published = Post.objects.create(author=cls.author, title='Public post', text='public body',
                                            published_date=timezone.now())

    def get_detail(self, post):
        return self.client.get(reverse('post_detail', kwargs={'pk': post.pk}))

    def test_anonymous_cannot_view_draft(self):
        self.assertEqual(self.get_detail(self.draft).status_code, 404)

    def test_other_user_cannot_view_draft(self):
        self.client.force_login(self.other)
        self.assertEqual(self.get_detail(self.draft).status_code, 404)

    def test_author_can_view_draft(self):
        self.client.force_login(self.author)
        self.assertContains(self.get_detail(self.draft), 'draft body')

    def test_admin_can_view_draft(self):
        self.client.force_login(self.admin)
        self.assertContains(self.get_detail(self.draft), 'draft body')

    def test_anonymous_can_view_published_post(self):
        self.assertContains(self.get_detail(self.published), 'public body')

    def test_anonymous_cannot_comment_on_draft(self):
        url = reverse('add_comment_to_post', kwargs={'pk': self.draft.pk})
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {'author': 'x', 'text': 'y'}).status_code, 404)
        self.assertFalse(self.draft.comments.exists())
