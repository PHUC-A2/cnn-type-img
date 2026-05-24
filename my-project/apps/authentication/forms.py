"""Form đăng ký, đăng nhập, profile — validation backend tiếng Việt."""

from pathlib import Path

from django import forms

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.avatar_storage_service import AvatarStorageService
from apps.authentication.services.password_service import PasswordService
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
    """Form cập nhật hồ sơ — email chỉ đọc, đổi mật khẩu có xác minh."""

    full_name = forms.CharField(
        max_length=100,
        required=False,
        label='Họ tên',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'data-field': 'full_name',
            'placeholder': 'Nguyễn Văn A',
        }),
    )
    username = forms.CharField(
        max_length=50,
        label='Tên đăng nhập',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'data-field': 'username',
            'autocomplete': 'username',
        }),
    )
    avatar = forms.FileField(
        required=False,
        label='Ảnh đại diện',
        widget=forms.ClearableFileInput(attrs={
            'class': 'sr-only',
            'data-field': 'avatar',
            'accept': 'image/jpeg,image/png,image/webp,image/gif',
        }),
    )
    new_password = forms.CharField(
        required=False,
        label='Mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'aurora-input',
            'data-field': 'new_password',
            'autocomplete': 'new-password',
            'placeholder': 'Để trống nếu không đổi',
        }),
    )
    confirm_password = forms.CharField(
        required=False,
        label='Xác nhận mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'aurora-input',
            'data-field': 'confirm_password',
            'autocomplete': 'new-password',
        }),
    )
    current_password = forms.CharField(
        required=False,
        label='Mật khẩu hiện tại',
        widget=forms.PasswordInput(attrs={
            'class': 'aurora-input',
            'data-field': 'current_password',
            'autocomplete': 'current-password',
        }),
    )
    use_password_recovery = forms.BooleanField(
        required=False,
        label='Quên mật khẩu hiện tại',
        widget=forms.CheckboxInput(attrs={
            'class': 'aurora-checkbox',
            'data-field': 'use_password_recovery',
        }),
    )
    recovery_username = forms.CharField(
        required=False,
        label='Xác minh tên đăng nhập',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'data-field': 'recovery_username',
            'placeholder': 'Nhập đúng tên đăng nhập của bạn',
            'autocomplete': 'off',
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 3:
            raise forms.ValidationError('Tên đăng nhập phải có ít nhất 3 ký tự.')
        if not validate_username_format(username):
            raise forms.ValidationError('Tên đăng nhập chỉ được dùng chữ, số và dấu gạch dưới.')
        if self.user and UserRepository.username_exists(username, exclude_id=self.user.id):
            raise forms.ValidationError('Tên đăng nhập đã tồn tại.')
        return username

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

    def clean(self):
        cleaned = super().clean()
        if not self.user:
            return cleaned

        new_password = cleaned.get('new_password', '')
        confirm_password = cleaned.get('confirm_password', '')
        current_password = cleaned.get('current_password', '')
        use_recovery = cleaned.get('use_password_recovery')
        recovery_username = (cleaned.get('recovery_username') or '').strip()

        if new_password or confirm_password:
            if not new_password:
                self.add_error('new_password', 'Vui lòng nhập mật khẩu mới.')
            elif len(new_password) < 6:
                self.add_error('new_password', 'Mật khẩu mới phải có ít nhất 6 ký tự.')
            if new_password != confirm_password:
                self.add_error('confirm_password', 'Mật khẩu xác nhận không khớp.')

            if new_password:
                if use_recovery:
                    if not recovery_username:
                        self.add_error('recovery_username', 'Vui lòng nhập tên đăng nhập để xác minh.')
                    elif recovery_username != self.user.username:
                        self.add_error('recovery_username', 'Tên đăng nhập xác minh không khớp.')
                elif not current_password:
                    self.add_error('current_password', 'Vui lòng nhập mật khẩu hiện tại.')
                elif not PasswordService.verify_password(current_password, self.user.password):
                    self.add_error('current_password', 'Mật khẩu hiện tại không đúng.')

        return cleaned

    def wants_password_change(self) -> bool:
        """Có yêu cầu đổi mật khẩu hay không."""
        return bool(self.cleaned_data.get('new_password'))
