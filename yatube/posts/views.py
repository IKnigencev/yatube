from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from .models import Follow, Post, Group, User, Comment
from .forms import PostForm, CommentForm


@cache_page(20)
def index(request):
    """Главная страница проекта.

    Выводит последние 10 постов.
    """
    post_list = Post.objects.select_related('author').all()

    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страницца групп.

    Выводит название, описание группы и последние 10 постов этой группы.
    """
    group = get_object_or_404(Group, slug=slug)

    posts_list = group.posts.all()

    paginator = Paginator(posts_list, 10)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница просмотра профиля автора.

    Выводиться информация о колличестве постов автора и сами посты.
    """
    user = get_object_or_404(User, username=username)

    posts_list = user.posts.all()

    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    is_author = not request.user == user

    following = user.following.exists()

    context = {
        'page_obj': page_obj,
        'author': user,
        'is_author': is_author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница просмотра отдельной записи.

    Видна вссе пользователям, которые перешли по ссылке.
    Если перешел авто поста, будет видна кнопка редактирования поста.
    """
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.select_related('author').filter(post=post)

    form = CommentForm(request.POST or None)
    if form.is_valid():
        return redirect('posts:add_comment', post_id)

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Страница создания нового поста.

    Обязательное поле текста поста и необязательное поле группы,
    автор поста береться из request. Сохранение в модель Post.
    """

    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования поста.

    Видна только автору поста, другие пользователи
    перенаправляются на страницу просмотра записи.
    """
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    is_edit = True
    return render(
        request,
        'posts/create_post.html',
        {'is_edit': is_edit, 'form': form})


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница с постами авторов на которых подписан user."""
    author_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(author_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    author = get_object_or_404(User, username=username)
    user = request.user
    if request.user.username != username:
        Follow.objects.select_related('author').get_or_create(
            author=author,
            user=user
        )
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=user).delete()
    return redirect('posts:profile', username)
