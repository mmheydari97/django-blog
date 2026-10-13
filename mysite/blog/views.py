from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.views.generic import (TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView)

from blog.models import Post, Comment
from blog.forms import PostForm, CommentForm

# Create your views here.

COMMENT_LIMIT = 5          # comments allowed per visitor IP...
COMMENT_WINDOW = 10 * 60   # ...in this many seconds


def managed_posts(user):
    """Posts the user may edit, publish, delete or moderate: their own, or all of them for admins."""
    if user.is_superuser:
        return Post.objects.all()
    return Post.objects.filter(author_id=user.pk)


def can_manage(user, post):
    return user.is_superuser or post.author_id == user.pk


def visible_posts(user):
    """Published posts, plus the drafts the user manages."""
    return Post.objects.filter(published_date__lte=timezone.now()) | managed_posts(user)


def client_ip(request):
    # PythonAnywhere's proxy passes the visitor's address in X-Real-IP; REMOTE_ADDR is the proxy.
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR')


def comment_rate_limited(request):
    """Counts a comment against the visitor's IP and says whether they're over the limit."""
    key = 'comment-count:{}'.format(client_ip(request))
    cache.add(key, 0, COMMENT_WINDOW)
    try:
        return cache.incr(key) > COMMENT_LIMIT
    except ValueError:  # the key expired between add() and incr()
        cache.add(key, 1, COMMENT_WINDOW)
        return False


class ManagedPostMixin(LoginRequiredMixin):
    """Limits a post view to the post's author and admins; anyone else gets a 404."""

    def get_queryset(self):
        return managed_posts(self.request.user)


class AboutView(TemplateView):
    template_name = 'about.html'


class PostListView(ListView):
    model = Post

    def get_queryset(self):
        return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')


class PostDetailView(DetailView):
    model = Post

    def get_queryset(self):
        return visible_posts(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage'] = can_manage(self.request.user, self.object)
        return context


class CreatePostView(LoginRequiredMixin, CreateView):
    login_url = '/accounts/login/'
    redirect_field_name = 'blog/post_detail.html'

    form_class = PostForm

    model = Post

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(ManagedPostMixin, UpdateView):
    login_url = '/accounts/login/'
    redirect_field_name = 'blog/post_detail.html'

    form_class = PostForm

    model = Post


class PostDeleteView(ManagedPostMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')



class DraftListView(LoginRequiredMixin, ListView):
    login_url = '/accounts/login/'
    redirect_field_name = 'blog/post_list.html'
    model = Post
    template_name = 'blog/post_draft_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return managed_posts(self.request.user).filter(published_date__isnull=True).order_by('create_date')



#############################
#############################

@login_required
@require_POST
def post_publish(request, pk):
    post = get_object_or_404(managed_posts(request.user), pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)



def add_comment_to_post(request, pk):
    post = get_object_or_404(visible_posts(request.user), pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            if comment_rate_limited(request):
                form.add_error(None, "You're commenting too quickly. Please wait a few minutes and try again.")
            else:
                comment = form.save(commit=False)
                comment.post = post
                comment.save()
                return redirect('post_detail', pk=pk)
    else:
        form = CommentForm()
    return render(request, 'blog/comment_form.html', {'form':form})


@login_required
@require_POST
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk, post__in=managed_posts(request.user))
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)


@login_required
@require_POST
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk, post__in=managed_posts(request.user))
    post_pk = comment.post.pk
    comment.delete()
    return redirect('post_detail', pk=post_pk)
