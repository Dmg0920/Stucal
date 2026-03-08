import os
from django import forms
from django.conf import settings
from .models import Session, Material


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            'date', 'time_start', 'time_end', 'status',
            'planned_content', 'reminders', 'actual_content',
            'teacher_note', 'materials',
        ]
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date', 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500'}
            ),
            'time_start': forms.TimeInput(
                attrs={'type': 'time', 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500'}
            ),
            'time_end': forms.TimeInput(
                attrs={'type': 'time', 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500'}
            ),
            'status': forms.Select(
                attrs={'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500'}
            ),
            'planned_content': forms.Textarea(
                attrs={'rows': 4, 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '預計上課進度...'}
            ),
            'reminders': forms.Textarea(
                attrs={'rows': 3, 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '需要準備的事項、注意事項...'}
            ),
            'actual_content': forms.Textarea(
                attrs={'rows': 4, 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '實際上課內容紀錄...'}
            ),
            'teacher_note': forms.Textarea(
                attrs={'rows': 3, 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '老師私人備註（家長不可見）...'}
            ),
            'materials': forms.CheckboxSelectMultiple(),
        }
        labels = {
            'date': '上課日期',
            'time_start': '開始時間',
            'time_end': '結束時間',
            'status': '狀態',
            'planned_content': '預計進度',
            'reminders': '提醒事項',
            'actual_content': '實際上課內容',
            'teacher_note': '老師備註（僅老師可見）',
            'materials': '相關教材',
        }


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['title', 'subject', 'description', 'link', 'file']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '教材名稱'}
            ),
            'subject': forms.TextInput(
                attrs={'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '例：數學、英文'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 3, 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '教材說明...'}
            ),
            'link': forms.URLInput(
                attrs={'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': 'https://...'}
            ),
            'file': forms.ClearableFileInput(
                attrs={'class': 'w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer'}
            ),
        }
        labels = {
            'title': '教材名稱',
            'subject': '科目',
            'description': '說明',
            'link': '外部連結',
            'file': '上傳檔案',
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f:
            ext = os.path.splitext(f.name)[1].lower()
            allowed = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS',
                              ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.jpg', '.jpeg', '.png'])
            if ext not in allowed:
                raise forms.ValidationError(f'不支援的檔案格式，允許：{", ".join(allowed)}')
            max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 20 * 1024 * 1024)
            if f.size > max_size:
                raise forms.ValidationError(f'檔案過大，上限為 {max_size // 1024 // 1024} MB')
        return f


class LoginForm(forms.Form):
    ROLE_CHOICES = [
        ('parent', '家長'),
        ('teacher', '老師'),
    ]
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='身份',
        widget=forms.RadioSelect()
    )
    password = forms.CharField(
        required=False,
        label='老師密碼',
        widget=forms.PasswordInput(
            attrs={'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': '選擇老師身份時需輸入密碼'}
        )
    )
