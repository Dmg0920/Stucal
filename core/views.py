from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib import messages

from .models import Session, Material
from .forms import SessionForm, MaterialForm, LoginForm
from .decorators import teacher_required


def home(request):
    today = date.today()

    today_session = Session.objects.filter(date=today).exclude(status='cancelled').first()

    next_session = None
    days_until = None
    if not today_session:
        next_session = Session.objects.filter(
            date__gt=today, status='scheduled'
        ).order_by('date', 'time_start').first()
        if next_session:
            days_until = (next_session.date - today).days

    last_completed = Session.objects.filter(status='completed').order_by('-date', '-time_start').first()

    context = {
        'today': today,
        'today_session': today_session,
        'next_session': next_session,
        'days_until': days_until,
        'last_completed': last_completed,
        'role': request.session.get('role', 'parent'),
    }
    return render(request, 'core/home.html', context)


def calendar_view(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    import calendar
    cal = calendar.monthcalendar(year, month)

    sessions = Session.objects.filter(date__year=year, date__month=month).exclude(status='cancelled')
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

    # 每天第一個 session 的 pk，供月曆格子連結使用
    first_pk_by_day = {day: sessions[0].pk for day, sessions in session_dates.items()}

    context = {
        'calendar': cal,
        'year': year,
        'month': month,
        'month_name': month_names[month],
        'today': today,
        'session_dates': session_dates,
        'first_pk_by_day': first_pk_by_day,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'role': request.session.get('role', 'parent'),
    }
    return render(request, 'core/calendar.html', context)


def session_detail(request, pk):
    session = get_object_or_404(Session, pk=pk)
    role = request.session.get('role', 'parent')
    context = {
        'session': session,
        'role': role,
    }
    return render(request, 'core/session_detail.html', context)


@teacher_required
def session_edit(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, '課程已更新')
            return redirect('session_detail', pk=session.pk)
    else:
        form = SessionForm(instance=session)
    return render(request, 'core/session_form.html', {'form': form, 'session': session, 'action': '編輯課程'})


@teacher_required
def session_new(request):
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            messages.success(request, '課程已新增')
            return redirect('session_detail', pk=session.pk)
    else:
        form = SessionForm(initial={'date': date.today(), 'status': 'scheduled'})
    return render(request, 'core/session_form.html', {'form': form, 'session': None, 'action': '新增課程'})


def materials_list(request):
    materials = Material.objects.all()
    subject_filter = request.GET.get('subject', '')
    if subject_filter:
        materials = materials.filter(subject__icontains=subject_filter)

    subjects = Material.objects.values_list('subject', flat=True).distinct()
    context = {
        'materials': materials,
        'subjects': subjects,
        'subject_filter': subject_filter,
        'role': request.session.get('role', 'parent'),
    }
    return render(request, 'core/materials.html', context)


@teacher_required
def material_new(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '教材已新增')
            return redirect('materials_list')
    else:
        form = MaterialForm()
    return render(request, 'core/material_form.html', {'form': form, 'action': '新增教材'})


@teacher_required
def material_edit(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, '教材已更新')
            return redirect('materials_list')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'core/material_form.html', {'form': form, 'material': material, 'action': '編輯教材'})


def history(request):
    sessions = Session.objects.filter(status='completed').order_by('-date', '-time_start')
    context = {
        'sessions': sessions,
        'role': request.session.get('role', 'parent'),
    }
    return render(request, 'core/history.html', context)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            password = form.cleaned_data.get('password', '')

            if role == 'teacher':
                correct_password = getattr(settings, 'TEACHER_PASSWORD', 'teacher123')
                if password != correct_password:
                    form.add_error('password', '密碼錯誤')
                    return render(request, 'core/login.html', {'form': form})

            request.session['role'] = role
            messages.success(request, f'已切換為{"老師" if role == "teacher" else "家長"}身份')
            return redirect('home')
    else:
        form = LoginForm(initial={'role': request.session.get('role', 'parent')})

    return render(request, 'core/login.html', {'form': form, 'current_role': request.session.get('role', 'parent')})
