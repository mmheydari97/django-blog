from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Post, Comment
from blog.views import COMMENT_LIMIT


class BlogTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user('author', password='pw')
        cls.other = User.objects.create_user('other', password='pw')
        cls.admin = User.objects.create_superuser('admin', password='pw')
        cls.draft = Post.objects.create(author=cls.author, title='Secret draft', text='draft body')
        cls.published = Post.objects.create(author=cls.author, title='Public post', text='public body',
                                            published_date=timezone.now())
        cls.pending = Comment.objects.create(post=cls.published, author='visitor', text='pending comment')

    def setUp(self):
        cache.clear()


class DraftVisibilityTests(BlogTestCase):

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

    def test_draft_list_only_shows_own_drafts(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse('post_draft_list')), 'Secret draft')
        self.client.force_login(self.author)
        self.assertContains(self.client.get(reverse('post_draft_list')), 'Secret draft')


class PostPermissionTests(BlogTestCase):

    def url(self, name, obj):
        return reverse(name, kwargs={'pk': obj.pk})

    def test_other_user_cannot_edit_delete_or_publish(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url('post_edit', self.draft)).status_code, 404)
        self.assertEqual(self.client.post(self.url('post_edit', self.published),
                                          {'title': 'hacked', 'text': 'hacked'}).status_code, 404)
        self.assertEqual(self.client.post(self.url('post_remove', self.published)).status_code, 404)
        self.assertEqual(self.client.post(self.url('post_publish', self.draft)).status_code, 404)
        self.published.refresh_from_db()
        self.draft.refresh_from_db()
        self.assertEqual(self.published.title, 'Public post')
        self.assertIsNone(self.draft.published_date)

    def test_other_user_cannot_moderate_comments(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url('comment_approve', self.pending)).status_code, 404)
        self.assertEqual(self.client.post(self.url('comment_remove', self.pending)).status_code, 404)
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.approved_comment)

    def test_other_user_does_not_see_pending_comments_or_actions(self):
        self.client.force_login(self.other)
        response = self.client.get(self.url('post_detail', self.published))
        self.assertNotContains(response, 'pending comment')
        self.assertNotContains(response, self.url('post_edit', self.published))

    def test_author_can_edit_and_publish(self):
        self.client.force_login(self.author)
        self.client.post(self.url('post_edit', self.draft), {'title': 'Edited', 'text': 'body'})
        self.client.post(self.url('post_publish', self.draft))
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.title, 'Edited')
        self.assertIsNotNone(self.draft.published_date)

    def test_admin_can_moderate_and_delete(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url('post_detail', self.published))
        self.assertContains(response, 'pending comment')
        self.client.post(self.url('comment_approve', self.pending))
        self.pending.refresh_from_db()
        self.assertTrue(self.pending.approved_comment)
        self.client.post(self.url('post_remove', self.draft))
        self.assertFalse(Post.objects.filter(pk=self.draft.pk).exists())

    def test_new_post_author_is_the_logged_in_user(self):
        self.client.force_login(self.other)
        self.client.post(reverse('post_new'), {'author': self.admin.pk, 'title': 'Mine', 'text': 'body'})
        self.assertEqual(Post.objects.get(title='Mine').author, self.other)


class StateChangesRequirePostTests(BlogTestCase):
    """A link or redirect (GET) must not be able to publish posts or moderate comments."""

    def test_get_is_rejected(self):
        self.client.force_login(self.admin)
        for name, obj in (('post_publish', self.draft),
                          ('comment_approve', self.pending),
                          ('comment_remove', self.pending)):
            response = self.client.get(reverse(name, kwargs={'pk': obj.pk}))
            self.assertEqual(response.status_code, 405, name)
        self.draft.refresh_from_db()
        self.pending.refresh_from_db()
        self.assertIsNone(self.draft.published_date)
        self.assertFalse(self.pending.approved_comment)

    def test_post_without_csrf_token_is_rejected(self):
        self.client.force_login(self.admin)
        self.client.handler.enforce_csrf_checks = True
        response = self.client.post(reverse('post_publish', kwargs={'pk': self.draft.pk}))
        self.assertEqual(response.status_code, 403)


class RateLimitTests(BlogTestCase):

    def test_comments_are_rate_limited_per_ip(self):
        url = reverse('add_comment_to_post', kwargs={'pk': self.published.pk})
        for i in range(COMMENT_LIMIT):
            self.client.post(url, {'author': 'spammer', 'text': 'spam %d' % i})
        response = self.client.post(url, {'author': 'spammer', 'text': 'one too many'})
        self.assertContains(response, 'commenting too quickly')
        self.assertEqual(self.published.comments.filter(author='spammer').count(), COMMENT_LIMIT)

        # A different visitor is unaffected.
        self.client.post(url, {'author': 'someone', 'text': 'hi'}, HTTP_X_REAL_IP='203.0.113.9')
        self.assertTrue(self.published.comments.filter(author='someone').exists())

    def test_login_locks_out_after_repeated_failures(self):
        url = reverse('login')
        for _ in range(5):
            self.client.post(url, {'username': 'admin', 'password': 'wrong'})
        response = self.client.post(url, {'username': 'admin', 'password': 'pw'})
        self.assertEqual(response.status_code, 429)
        self.assertNotIn('_auth_user_id', self.client.session)

        # Other IPs can still log in.
        response = self.client.post(url, {'username': 'admin', 'password': 'pw'}, HTTP_X_REAL_IP='203.0.113.9')
        self.assertEqual(response.status_code, 302)
