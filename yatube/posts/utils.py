from django.core.paginator import Paginator


POSTS_COUNT = 10


def pagination(request, posts):
    paginator = Paginator(posts, POSTS_COUNT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
