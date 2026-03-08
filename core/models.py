import os
import secrets
from django.db import models
from django.contrib.auth.models import User


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    proof = models.TextField(verbose_name='上課證明', help_text='請描述您的教學背景或上課證明')
    is_approved = models.BooleanField(default=False, verbose_name='已審核')

    class Meta:
        verbose_name = '老師'
        verbose_name_plural = '老師'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username}'


class Student(models.Model):
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name='students', verbose_name='老師'
    )
    name = models.CharField(max_length=50, verbose_name='學生名稱')
    display_name = models.CharField(max_length=50, blank=True, verbose_name='學生自訂名稱')
    access_key = models.CharField(max_length=8, unique=True, verbose_name='加入密鑰')
    joined = models.BooleanField(default=False, verbose_name='已加入')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '學生'
        verbose_name_plural = '學生'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def shown_name(self):
        return self.display_name or self.name

    def save(self, *args, **kwargs):
        if not self.access_key:
            while True:
                key = secrets.token_urlsafe(6)[:8]
                if not Student.objects.filter(access_key=key).exists():
                    self.access_key = key
                    break
        super().save(*args, **kwargs)


class Material(models.Model):
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.CASCADE, related_name='materials',
        verbose_name='老師', null=True, blank=True
    )
    student = models.ForeignKey(
        Student, on_delete=models.SET_NULL, related_name='materials',
        verbose_name='指定學生（空白=共用）', null=True, blank=True
    )
    title = models.CharField(max_length=200, verbose_name='教材名稱')
    subject = models.CharField(max_length=100, verbose_name='科目')
    description = models.TextField(blank=True, verbose_name='說明')
    link = models.URLField(blank=True, verbose_name='連結')
    file = models.FileField(upload_to='materials/', blank=True, null=True, verbose_name='上傳檔案')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')

    class Meta:
        verbose_name = '教材'
        verbose_name_plural = '教材'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} - {self.title}'

    @property
    def file_name(self):
        if self.file:
            return os.path.basename(self.file.name)
        return None

    @property
    def file_ext(self):
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return None


class Session(models.Model):
    STATUS_CHOICES = [
        ('scheduled', '已排定'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='sessions',
        verbose_name='學生', null=True, blank=True
    )
    date = models.DateField(verbose_name='上課日期')
    time_start = models.TimeField(verbose_name='開始時間')
    time_end = models.TimeField(verbose_name='結束時間')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name='狀態'
    )
    planned_content = models.TextField(verbose_name='預計進度')
    reminders = models.TextField(blank=True, verbose_name='提醒事項')
    actual_content = models.TextField(blank=True, verbose_name='實際上課內容')
    teacher_note = models.TextField(blank=True, verbose_name='老師備註')
    materials = models.ManyToManyField(
        Material,
        blank=True,
        verbose_name='教材',
        related_name='sessions'
    )

    class Meta:
        verbose_name = '課程'
        verbose_name_plural = '課程'
        ordering = ['-date', '-time_start']

    def __str__(self):
        return f'{self.date} {self.time_start} ({self.get_status_display()})'

    @property
    def duration_minutes(self):
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.time_start)
        end = datetime.combine(date.today(), self.time_end)
        return int((end - start).total_seconds() / 60)
