"""Form đăng ký, đăng nhập, profile — validation backend tiếng Việt."""

from pathlib import Path

from django import forms

from apps.authentication.services.avatar_storage_service import AvatarStorageService
from apps.authentication.validators import validate_email_format, validate_username_format


class RegisterForm(forms.Form):
    """Form đăng ký tài khoản mới."""

    username = forms.CharField(
        max_length=50,
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Nhập tên đăng nhập',
            'autocomplete': 'username',
            'data-field': 'username',
        }),
    )
    email = forms.CharField(
        max_length=100,
        label='Email',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'email@example.com',
            'autocomplete': 'email',
            'data-field': 'email',
        }),
    )
    full_name = forms.CharField(
        max_length=100,
        required=False,
        label='Họ tên',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Nguyễn Văn A',
            'data-field': 'full_name',
        }),
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Ít nhất 6 ký tự',
            'autocomplete': 'new-password',
            'data-field': 'password',
        }),
    )
    password_confirm = forms.CharField(
        label='Xác nhận mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Nhập lại mật khẩu',
            'autocomplete': 'new-password',
            'data-field': 'password_confirm',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Tên đăng nhập phải có ít nhất 3 ký tự.')
        if not validate_username_format(username):
            raise forms.ValidationError('Tên đăng nhập chỉ được dùng chữ, số và dấu gạch dưới.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not validate_email_format(email):
            raise forms.ValidationError('Email không hợp lệ.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 6:
            raise forms.ValidationError('Mật khẩu phải có ít nhất 6 ký tự.')
        return password

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Mật khẩu xác nhận không khớp.')
        return cleaned


class LoginForm(forms.Form):
    """Form đăng nhập."""

    username = forms.CharField(
        max_length=100,
        label='Tên đăng nhập hoặc Email',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Tên đăng nhập hoặc email',
            'autocomplete': 'username',
            'data-field': 'username',
        }),
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Nhập mật khẩu',
            'autocomplete': 'current-password',
            'data-field': 'password',
        }),
    )
    remember_me = forms.BooleanField(
        required=False,
        label='Ghi nhớ đăng nhập',
        widget=forms.CheckboxInput(attrs={'class': 'aurora-checkbox', 'data-field': 'remember_me'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError('Vui lòng nhập tên đăng nhập hoặc email.')
        return username

    def clean_password(self):
        password = self.cleaned_data['password']
        if not password:
            raise forms.ValidationError('Vui lòng nhập mật khẩu.')
        return password


class ProfileForm(forms.Form):
    """Form cập nhật thông tin cá nhân."""

    full_name = forms.CharField(
        max_length=100,
        required=False,
        label='Họ tên',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'data-field': 'full_name',
        }),
    )
    email = forms.CharField(
        max_length=100,
        label='Email',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'data-field': 'email',
        }),
    )
    avatar = forms.FileField(
        required=False,
        label='Ảnh đại diện',
        widget=forms.ClearableFileInput(attrs={
            'class': 'aurora-file',
            'data-field': 'avatar',
            'accept': '',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not validate_email_format(email):
            raise forms.ValidationError('Email không hợp lệ.')
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar

        ext = Path(avatar.name).suffix.lower()
        if ext not in AvatarStorageService.ALLOWED_EXTENSIONS:
            raise forms.ValidationError('Chỉ chấp nhận ảnh JPG, PNG, WEBP, GIF.')

        if avatar.size > AvatarStorageService.MAX_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(
                f'Ảnh không được vượt quá {AvatarStorageService.MAX_SIZE_MB}MB.'
            )
        return avatar
