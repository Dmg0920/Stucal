from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Session, Material, TeacherProfile, Student
from .forms import (
    SessionForm, MaterialForm, LoginForm,
    TeacherRegisterForm, TeacherLoginForm,
    StudentForm, StudentJoinForm, StudentSetNameForm,
)
from .decorators import teacher_login_required, student_selected_required, student_login_required


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_teacher(request):
    """從 session 取得 TeacherProfile，若不存在回傳 None"""
    tid = request.session.get('teacher_id')
    if not tid:
        return None
    try:
        return TeacherProfile.objects.get(pk=tid)
    except TeacherProfile.DoesNotExist:
        return None


def get_current_student(request):
    """從 session 取得目前選中的 Student，若不存在回傳 None"""
    sid = request.session.get('current_student_id')
    if not sid:
        return None
    try:
        return Student.objects.get(pk=sid)
    except Student.DoesNotExist:
        return None


def base_context(request):
    """所有 view 通用的 context 資料"""
    teacher = get_teacher(request)
    current_student = get_current_student(request) if teacher else None
    student_role = request.session.get('student_role')
    student_key = request.session.get('student_key')
    student_obj = None
    if student_role == 'student' and student_key:
        try:
            student_obj = Student.objects.get(access_key=student_key)
        except Student.DoesNotExist:
            pass
    return {
        'teacher': teacher,
        'current_student': current_student,
        'student_obj': student_obj,
        'role': 'teacher' if teacher else ('student' if student_role == 'student' else 'guest'),
    }


# ── Landing ───────────────────────────────────────────────────────────────────

def landing(request):
    # 已登入老師 → 跳轉首頁（需先選學生）
    if request.session.get('teacher_id'):
        if request.session.get('current_student_id'):
            return redirect('home')
        return redirect('student_list')
    # 學生已登入 → 跳轉首頁
    if request.session.get('student_role') == 'student':
        return redirect('home')
    return render(request, 'core/landing.html')


# ── Teacher Auth ──────────────────────────────────────────────────────────────

def teacher_register(request):
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = User.objects.create_user(
                username=cd['username'],
                password=cd['password1'],
                is_active=False,  # 等待管理員審核
            )
            # 設定全名
            names = cd['full_name'].strip().split(' ', 1)
            user.first_name = names[0]
            user.last_name = names[1] if len(names) > 1 else ''
            user.save()
            TeacherProfile.objects.create(user=user, proof=cd['proof'])
            return redirect('teacher_pending')
    else:
        form = TeacherRegisterForm()
    return render(request, 'core/teacher_register.html', {'form': form})


def teacher_pending(request):
    return render(request, 'core/teacher_pending.html')


def teacher_login(request):
    if request.method == 'POST':
        form = TeacherLoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is None:
                form.add_error(None, '帳號或密碼錯誤')
            elif not user.is_active:
                return redirect('teacher_pending')
            else:
                try:
                    profile = user.teacher_profile
                    if not profile.is_approved:
                        return redirect('teacher_pending')
                    request.session['teacher_id'] = profile.pk
                    # 清除學生端 session
                    request.session.pop('student_role', None)
                    request.session.pop('student_key', None)
                    messages.success(request, f'歡迎回來，{profile}！')
                    return redirect('student_list')
                except TeacherProfile.DoesNotExist:
                    form.add_error(None, '此帳號尚未建立老師資料，請聯繫管理員')
    else:
        form = TeacherLoginForm()
    return render(request, 'core/teacher_login.html', {'form': form})


@teacher_login_required
def teacher_logout(request):
    request.session.flush()
    return redirect('landing')


# ── Student Management (Teacher Side) ────────────────────────────────────────

@teacher_login_required
def student_list(request):
    teacher = get_teacher(request)
    students = teacher.students.all()
    current_student = get_current_student(request)
    ctx = base_context(request)
    ctx.update({'students': students, 'current_student': current_student})
    return render(request, 'core/student_list.html', ctx)


@teacher_login_required
def student_add(request):
    teacher = get_teacher(request)
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.teacher = teacher
            student.save()
            messages.success(request, f'學生「{student.name}」已建立，密鑰：{student.access_key}')
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'core/student_form.html', {'form': form, 'action': '新增學生'})


@teacher_login_required
def student_select(request, pk):
    teacher = get_teacher(request)
    student = get_object_or_404(Student, pk=pk, teacher=teacher)
    request.session['current_student_id'] = student.pk
    messages.success(request, f'已切換至學生：{student.shown_name}')
    return redirect('home')


# ── Student Auth (Student Side) ───────────────────────────────────────────────

def student_join(request):
    if request.method == 'POST':
        form = StudentJoinForm(request.POST)
        if form.is_valid():
            key = form.cleaned_data['access_key'].strip()
            try:
                student = Student.objects.get(access_key=key)
                request.session['student_key'] = student.access_key
                request.session['student_role'] = 'student'
                # 清除老師端 session
                request.session.pop('teacher_id', None)
                request.session.pop('current_student_id', None)
                if not student.joined:
                    return redirect('student_setname')
                messages.success(request, f'歡迎回來，{student.shown_name}！')
                return redirect('home')
            except Student.DoesNotExist:
                form.add_error('access_key', '密鑰錯誤，請確認後重試')
    else:
        form = StudentJoinForm()
    return render(request, 'core/student_join.html', {'form': form})


@student_login_required
def student_setname(request):
    key = request.session.get('student_key')
    student = get_object_or_404(Student, access_key=key)
    if request.method == 'POST':
        form = StudentSetNameForm(request.POST)
        if form.is_valid():
            student.display_name = form.cleaned_data['display_name']
            student.joined = True
            student.save()
            messages.success(request, f'設定成功，歡迎加入 Stucal！')
            return redirect('home')
    else:
        form = StudentSetNameForm(initial={'display_name': student.display_name})
    return render(request, 'core/student_setname.html', {'form': form, 'student': student})


def student_logout(request):
    request.session.pop('student_role', None)
    request.session.pop('student_key', None)
    return redirect('student_join')


# ── Main Views ────────────────────────────────────────────────────────────────

def _require_auth(request):
    """
    回傳 (teacher, student, role, redirect_response)
    若需要 redirect，redirect_response 不為 None。
    """
    teacher = get_teacher(request)
    if teacher:
        student = get_current_student(request)
        if not student:
            return None, None, 'teacher', redirect('student_list')
        return teacher, student, 'teacher', None

    if request.session.get('student_role') == 'student':
        key = request.session.get('student_key')
        try:
            student = Student.objects.get(access_key=key)
            return student.teacher, student, 'student', None
        except Student.DoesNotExist:
            pass

    return None, None, 'guest', redirect('landing')


def home(request):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir

    today = date.today()
    qs = Session.objects.filter(student=student)
    today_session = qs.filter(date=today).exclude(status='cancelled').first()

    next_session = None
    days_until = None
    if not today_session:
        next_session = qs.filter(date__gt=today, status='scheduled').order_by('date', 'time_start').first()
        if next_session:
            days_until = (next_session.date - today).days

    last_completed = qs.filter(status='completed').order_by('-date', '-time_start').first()

    ctx = base_context(request)
    ctx.update({
        'today': today,
        'today_session': today_session,
        'next_session': next_session,
        'days_until': days_until,
        'last_completed': last_completed,
    })
    return render(request, 'core/home.html', ctx)


def calendar_view(request):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir

    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    import calendar as cal_module
    cal = cal_module.monthcalendar(year, month)

    sessions = Session.objects.filter(student=student, date__year=year, date__month=month).exclude(status='cancelled')
    session_dates = {}
    for s in sessions:
        day = s.date.day
        if day not in session_dates:
            session_dates[day] = []
        session_dates[day].append(s)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    month_names = ['', '一月', '二月', '三月', '四月', '五月', '六月',
                   '七月', '八月', '九月', '十月', '十一月', '十二月']

    first_pk_by_day = {day: sessions_list[0].pk for day, sessions_list in session_dates.items()}

    ctx = base_context(request)
    ctx.update({
        'calendar': cal, 'year': year, 'month': month,
        'month_name': month_names[month], 'today': today,
        'session_dates': session_dates, 'first_pk_by_day': first_pk_by_day,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
    })
    return render(request, 'core/calendar.html', ctx)


def session_detail(request, pk):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    session = get_object_or_404(Session, pk=pk, student=student)
    ctx = base_context(request)
    ctx['session'] = session
    return render(request, 'core/session_detail.html', ctx)


def session_edit(request, pk):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    if role != 'teacher':
        return redirect('session_detail', pk=pk)
    session = get_object_or_404(Session, pk=pk, student=student)
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session, teacher=teacher, student=student)
        if form.is_valid():
            form.save()
            messages.success(request, '課程已更新')
            return redirect('session_detail', pk=session.pk)
    else:
        form = SessionForm(instance=session, teacher=teacher, student=student)
    return render(request, 'core/session_form.html', {'form': form, 'session': session, 'action': '編輯課程', **base_context(request)})


def session_delete(request, pk):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    if role != 'teacher':
        return redirect('session_detail', pk=pk)
    session = get_object_or_404(Session, pk=pk, student=student)
    if request.method == 'POST':
        session.delete()
        messages.success(request, '課程已刪除')
        return redirect('calendar')
    return redirect('session_detail', pk=pk)


def session_new(request):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    if role != 'teacher':
        return redirect('home')
    if request.method == 'POST':
        form = SessionForm(request.POST, teacher=teacher, student=student)
        if form.is_valid():
            session = form.save(commit=False)
            session.student = student
            session.save()
            form.save_m2m()
            messages.success(request, '課程已新增')
            return redirect('session_detail', pk=session.pk)
    else:
        form = SessionForm(initial={'date': date.today(), 'status': 'scheduled'}, teacher=teacher, student=student)
    return render(request, 'core/session_form.html', {'form': form, 'session': None, 'action': '新增課程', **base_context(request)})


def materials_list(request):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir

    materials = Material.objects.filter(teacher=teacher).filter(
        Q(student=None) | Q(student=student)
    )
    subject_filter = request.GET.get('subject', '')
    if subject_filter:
        materials = materials.filter(subject__icontains=subject_filter)

    subjects = Material.objects.filter(teacher=teacher).values_list('subject', flat=True).distinct()
    ctx = base_context(request)
    ctx.update({'materials': materials, 'subjects': subjects, 'subject_filter': subject_filter})
    return render(request, 'core/materials.html', ctx)


def material_new(request):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    if role != 'teacher':
        return redirect('materials_list')
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            material = form.save(commit=False)
            material.teacher = teacher
            material.save()
            messages.success(request, '教材已新增')
            return redirect('materials_list')
    else:
        form = MaterialForm(teacher=teacher)
    return render(request, 'core/material_form.html', {'form': form, 'action': '新增教材', **base_context(request)})


def material_edit(request, pk):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    if role != 'teacher':
        return redirect('materials_list')
    material = get_object_or_404(Material, pk=pk, teacher=teacher)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, '教材已更新')
            return redirect('materials_list')
    else:
        form = MaterialForm(instance=material, teacher=teacher)
    return render(request, 'core/material_form.html', {'form': form, 'material': material, 'action': '編輯教材', **base_context(request)})


def material_delete(request, pk):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    if role != 'teacher':
        return redirect('materials_list')
    material = get_object_or_404(Material, pk=pk, teacher=teacher)
    if request.method == 'POST':
        material.delete()
        messages.success(request, '教材已刪除')
        return redirect('materials_list')
    return redirect('materials_list')


def history(request):
    teacher, student, role, redir = _require_auth(request)
    if redir:
        return redir
    sessions = Session.objects.filter(student=student, status='completed').order_by('-date', '-time_start')
    ctx = base_context(request)
    ctx['sessions'] = sessions
    return render(request, 'core/history.html', ctx)


# ── 舊 login view 保留（現在只做 redirect）───────────────────────────────────

def login_view(request):
    return redirect('teacher_login')
