from functools import wraps
from django.shortcuts import redirect


def teacher_login_required(view_func):
    """老師必須透過帳號登入（session 中有 teacher_id）"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('teacher_id'):
            return redirect('teacher_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_selected_required(view_func):
    """老師必須已選擇當前學生（session 中有 current_student_id）"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('teacher_id'):
            return redirect('teacher_login')
        if not request.session.get('current_student_id'):
            return redirect('student_list')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_login_required(view_func):
    """學生必須透過密鑰登入（session 中有 student_role == 'student'）"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('student_role') != 'student':
            return redirect('student_join')
        return view_func(request, *args, **kwargs)
    return wrapper


# 保留舊 decorator 別名，供相容性使用
def teacher_required(view_func):
    return teacher_login_required(view_func)
