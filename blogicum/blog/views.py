"""Views for the blog application."""
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post

User = get_user_model()
POSTS_PER_PAGE = 10


def get_posts_queryset():
    """Возвращает отфильтрованные опубликованные посты."""
    return Post.objects.select_related(
        'category',
        'location',
        'author',
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ).annotate(
        comment_count=Count('comments'),
    ).order_by('-pub_date')


def paginate_posts(request, posts, per_page=POSTS_PER_PAGE):
    """Разбивает публикации на страницы."""
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    """Главная страница: отображает последние опубликованные посты."""
    posts = get_posts_queryset()
    page_obj = paginate_posts(request, posts)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request, category_slug):
    """Страница категории: публикации выбранной категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    posts = category.posts.select_related(
        'location',
        'author',
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
    ).annotate(
        comment_count=Count('comments'),
    ).order_by('-pub_date')
    page_obj = paginate_posts(request, posts)
    return render(
        request,
        'blog/category.html',
        {
            'category': category,
            'page_obj': page_obj,
        },
    )


def profile(request, username):
    """Страница профиля пользователя со списком его публикаций."""
    author = get_object_or_404(User, username=username)
    if request.user == author:
        posts = author.posts.select_related(
            'category',
            'location',
        ).annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')
    else:
        posts = author.posts.select_related(
            'category',
            'location',
        ).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        ).annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')
    page_obj = paginate_posts(request, posts)
    return render(
        request,
        'blog/profile.html',
        {
            'profile': author,
            'page_obj': page_obj,
        },
    )


def post_detail(request, post_id):
    """Страница отдельной публикации с комментариями."""
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        pk=post_id,
    )
    if request.user != post.author:
        if (
            not post.is_published
            or not (post.category and post.category.is_published)
            or post.pub_date > timezone.now()
        ):
            raise Http404('Публикация не найдена')
    comments = post.comments.select_related('author').order_by('created_at')
    form = CommentForm()
    return render(
        request,
        'blog/detail.html',
        {
            'post': post,
            'form': form,
            'comments': comments,
        },
    )


@login_required
def create_post(request):
    """Создание новой публикации."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование публикации автором."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required
def delete_post(request, post_id):
    """Удаление публикации автором."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = PostForm(instance=post)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required
def edit_profile(request):
    """Редактирование профиля текущего пользователя."""
    form = ProfileEditForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def add_comment(request, post_id):
    """Добавление комментария к публикации."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария автором."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        'blog/comment.html',
        {
            'comment': comment,
            'form': form,
        },
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария автором."""
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})
