from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('role') != 'teacher':
            return HttpResponseForbidden(
                '<h1>403 禁止存取</h1><p>此功能僅限老師使用。<a href="/login/">切換身份</a></p>'
            )
        return view_func(request, *args, **kwargs)
    return wrapper
