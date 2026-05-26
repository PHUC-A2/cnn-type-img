"""Form admin panel — validation tiếng Việt."""

from django import forms

from apps.authentication.models import User
from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.validators import validate_email_format, validate_username_format
from apps.monitoring.services.admin_resource_service import AdminResourceService
from core.enums.user_role import UserRole


class AdminSearchForm(forms.Form):
    """Form tìm kiếm chung — GET."""

    q = forms.CharField(
        required=False,
        label='Tìm kiếm',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Từ khóa...',
        }),
    )
    include_inactive = forms.BooleanField(
        required=False,
        initial=True,
        label='Hiện bản ghi đã vô hiệu',
        widget=forms.CheckboxInput(attrs={'class': 'aurora-checkbox'}),
    )


class AdminTrainingFilterForm(forms.Form):
    """Lọc job huấn luyện."""

    q = forms.CharField(
        required=False,
        label='Tìm kiếm',
        widget=forms.TextInput(attrs={'class': 'aurora-input', 'placeholder': 'Model, dataset, user...'}),
    )
    status = forms.ChoiceField(
        required=False,
        label='Trạng thái',
        choices=[],
        widget=forms.Select(attrs={'class': 'aurora-input'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('', '— Tất cả —')] + AdminResourceService.training_status_choices()


class AdminPredictionFilterForm(forms.Form):
    """Lọc predictions admin."""

    q = forms.CharField(
        required=False,
        label='Tìm kiếm',
        widget=forms.TextInput(attrs={'class': 'aurora-input', 'placeholder': 'Nhãn, ảnh, user...'}),
    )
    user_id = forms.ChoiceField(
        required=False,
        label='Người dùng',
        choices=[],
        widget=forms.Select(attrs={'class': 'aurora-input'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', '— Tất cả người dùng —')]
        choices += [
            (str(u.id), u.get_display_name())
            for u in User.objects.filter(is_active=True).order_by('username')
        ]
        self.fields['user_id'].choices = choices


class AdminUserCreateForm(forms.Form):
    """Tạo user mới — admin."""

    username = forms.CharField(max_length=50, label='Tên đăng nhập', widget=forms.TextInput(attrs={'class': 'aurora-input'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'aurora-input'}))
    full_name = forms.CharField(required=False, max_length=100, label='Họ tên', widget=forms.TextInput(attrs={'class': 'aurora-input'}))
    password = forms.CharField(label='Mật khẩu', widget=forms.PasswordInput(attrs={'class': 'aurora-input'}))
    password_confirm = forms.CharField(label='Xác nhận mật khẩu', widget=forms.PasswordInput(attrs={'class': 'aurora-input'}))
    role = forms.ChoiceField(label='Vai trò', choices=UserRole.choices(), widget=forms.Select(attrs={'class': 'aurora-input'}))

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password', '')
        pw2 = cleaned.get('password_confirm', '')
        if pw and pw2 and pw != pw2:
            self.add_error('password_confirm', 'Mật khẩu xác nhận không khớp.')
        return cleaned


class AdminUserEditForm(forms.Form):
    """Sửa user — admin (email chỉ đọc, hiển thị ngoài form)."""

    username = forms.CharField(max_length=50, label='Tên đăng nhập', widget=forms.TextInput(attrs={'class': 'aurora-input'}))
    full_name = forms.CharField(required=False, max_length=100, label='Họ tên', widget=forms.TextInput(attrs={'class': 'aurora-input'}))
    role = forms.ChoiceField(label='Vai trò', choices=UserRole.choices(), widget=forms.Select(attrs={'class': 'aurora-input'}))
    is_active = forms.BooleanField(required=False, label='Đang kích hoạt', widget=forms.CheckboxInput(attrs={'class': 'aurora-checkbox'}))
    new_password = forms.CharField(required=False, label='Mật khẩu mới', widget=forms.PasswordInput(attrs={'class': 'aurora-input'}))

    def __init__(self, *args, user: User | None = None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)


class AdminDatasetForm(forms.Form):
    """Sửa dataset — admin."""

    dataset_name = forms.CharField(max_length=100, label='Tên bộ dữ liệu', widget=forms.TextInput(attrs={'class': 'aurora-input'}))
    description = forms.CharField(required=False, label='Mô tả', widget=forms.Textarea(attrs={'class': 'aurora-input', 'rows': 3}))
    is_active = forms.BooleanField(required=False, label='Đang kích hoạt', widget=forms.CheckboxInput(attrs={'class': 'aurora-checkbox'}))


class AdminModelForm(forms.Form):
    """Sửa mô hình CNN — admin."""

    model_name = forms.CharField(max_length=100, label='Tên mô hình', widget=forms.TextInput(attrs={'class': 'aurora-input'}))
    description = forms.CharField(required=False, label='Mô tả', widget=forms.Textarea(attrs={'class': 'aurora-input', 'rows': 3}))
    is_active = forms.BooleanField(required=False, label='Đang kích hoạt', widget=forms.CheckboxInput(attrs={'class': 'aurora-checkbox'}))
