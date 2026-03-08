import os
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from .models import Session, Material, Student, TeacherProfile

INPUT_CLASS = 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500'
TEXTAREA_CLASS = INPUT_CLASS


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            'date', 'time_start', 'time_end', 'status',
            'planned_content', 'reminders', 'actual_content',
            'teacher_note', 'materials',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'time_start': forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASS}),
            'time_end': forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASS}),
            'status': forms.Select(attrs={'class': INPUT_CLASS}),
            'planned_content': forms.Textarea(attrs={'rows': 4, 'class': TEXTAREA_CLASS, 'placeholder': '預計上課進度...'}),
            'reminders': forms.Textarea(attrs={'rows': 3, 'class': TEXTAREA_CLASS, 'placeholder': '需要準備的事項、注意事項...'}),
            'actual_content': forms.Textarea(attrs={'rows': 4, 'class': TEXTAREA_CLASS, 'placeholder': '實際上課內容紀錄...'}),
            'teacher_note': forms.Textarea(attrs={'rows': 3, 'class': TEXTAREA_CLASS, 'placeholder': '老師私人備註（家長不可見）...'}),
            'materials': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'date': '上課日期', 'time_start': '開始時間', 'time_end': '結束時間',
            'status': '狀態', 'planned_content': '預計進度', 'reminders': '提醒事項',
            'actual_content': '實際上課內容', 'teacher_note': '老師備註（僅老師可見）', 'materials': '相關教材',
        }

    def __init__(self, *args, teacher=None, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher and student:
            # 只顯示這位老師、這位學生（共用 or 指定）可用的教材
            from django.db.models import Q
            self.fields['materials'].queryset = Material.objects.filter(teacher=teacher).filter(
                Q(student=None) | Q(student=student)
            )
        elif teacher:
            self.fields['materials'].queryset = Material.objects.filter(teacher=teacher)


class MaterialForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        required=False,
        empty_label='共用所有學生',
        label='指定學生',
        widget=forms.Select(attrs={'class': INPUT_CLASS}),
    )

    class Meta:
        model = Material
        fields = ['title', 'subject', 'description', 'link', 'file', 'student']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '教材名稱'}),
            'subject': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '例：數學、英文'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': TEXTAREA_CLASS, 'placeholder': '教材說明...'}),
            'link': forms.URLInput(attrs={'class': INPUT_CLASS, 'placeholder': 'https://...'}),
            'file': forms.ClearableFileInput(
                attrs={'class': 'w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer'}
            ),
        }
        labels = {
            'title': '教材名稱', 'subject': '科目', 'description': '說明',
            'link': '外部連結', 'file': '上傳檔案',
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['student'].queryset = teacher.students.all()

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f and hasattr(f, 'name'):
            ext = os.path.splitext(f.name)[1].lower()
            allowed = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS',
                              ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.jpg', '.jpeg', '.png'])
            if ext not in allowed:
                raise forms.ValidationError(f'不支援的檔案格式，允許：{", ".join(allowed)}')
            max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 20 * 1024 * 1024)
            if f.size > max_size:
                raise forms.ValidationError(f'檔案過大，上限為 {max_size // 1024 // 1024} MB')
        return f


class TeacherRegisterForm(forms.Form):
    username = forms.CharField(
        label='帳號', max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '登入帳號（英數字）'}),
    )
    password1 = forms.CharField(
        label='密碼', widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': '至少 8 個字元'}),
    )
    password2 = forms.CharField(
        label='確認密碼', widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': '再次輸入密碼'}),
    )
    full_name = forms.CharField(
        label='真實姓名', max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '您的姓名'}),
    )
    proof = forms.CharField(
        label='上課證明',
        widget=forms.Textarea(attrs={'rows': 4, 'class': TEXTAREA_CLASS, 'placeholder': '請描述您的教學背景、科目、經驗等，供管理員審核...'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('此帳號已被使用')
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', '兩次密碼不一致')
        if p1 and len(p1) < 8:
            self.add_error('password1', '密碼至少需要 8 個字元')
        return cleaned_data


class TeacherLoginForm(forms.Form):
    username = forms.CharField(
        label='帳號',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '登入帳號'}),
    )
    password = forms.CharField(
        label='密碼',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': '密碼'}),
    )


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '例：小明'}),
        }
        labels = {'name': '學生名稱'}


class StudentJoinForm(forms.Form):
    access_key = forms.CharField(
        label='加入密鑰', max_length=8,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': '8 碼密鑰',
            'autocomplete': 'off',
            'style': 'letter-spacing: 0.2em; font-size: 20px; text-align: center;',
        }),
    )


class StudentSetNameForm(forms.Form):
    display_name = forms.CharField(
        label='你的名字', max_length=50,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '你想讓老師怎麼稱呼你？'}),
    )


# 舊的 LoginForm 保留，避免 import 錯誤（實際上不再用）
class LoginForm(forms.Form):
    ROLE_CHOICES = [('parent', '家長'), ('teacher', '老師')]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='身份', widget=forms.RadioSelect())
    password = forms.CharField(required=False, label='老師密碼', widget=forms.PasswordInput(attrs={'class': INPUT_CLASS}))
