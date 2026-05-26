"""Form upload ảnh phân loại."""

from django import forms

from apps.authentication.models import User
from apps.predictions.services.prediction_service import PredictionService
from apps.predictions.services.prediction_storage_service import PredictionStorageService


class PredictForm(forms.Form):
    """Form chọn model và upload ảnh."""

    model_id = forms.ChoiceField(
        label='Mô hình CNN',
        choices=[],
        widget=forms.Select(attrs={
            'class': 'aurora-input',
            'data-field': 'model_id',
        }),
    )
    image = forms.ImageField(
        label='Ảnh cần phân loại',
        widget=forms.ClearableFileInput(attrs={
            'class': 'hidden',
            'data-field': 'image',
            'accept': 'image/jpeg,image/png,image/webp,image/gif,image/bmp',
        }),
    )
    top_k = forms.IntegerField(
        required=False,
        initial=3,
        min_value=1,
        max_value=20,
        label='Top-K',
        widget=forms.NumberInput(attrs={
            'class': 'aurora-input',
            'data-field': 'top_k',
            'placeholder': '3',
        }),
    )

    def __init__(self, *args, user: User | None = None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        choices = []
        if user:
            for cnn in PredictionService.list_ready_models(user):
                choices.append((str(cnn.id), cnn.model_name))
        self.fields['model_id'].choices = choices

    def clean_model_id(self):
        value = self.cleaned_data['model_id']
        if not value:
            raise forms.ValidationError('Vui lòng chọn mô hình CNN.')
        return int(value)

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise forms.ValidationError('Vui lòng chọn ảnh cần phân loại.')

        ext = f'.{image.name.rsplit(".", 1)[-1].lower()}'
        if ext not in PredictionStorageService.ALLOWED_EXTENSIONS:
            raise forms.ValidationError('Chỉ chấp nhận ảnh JPG, PNG, WEBP, GIF, BMP.')

        max_bytes = PredictionStorageService.MAX_SIZE_MB * 1024 * 1024
        if image.size > max_bytes:
            raise forms.ValidationError(
                f'Ảnh không được vượt quá {PredictionStorageService.MAX_SIZE_MB}MB.'
            )
        return image

    def clean_top_k(self):
        value = self.cleaned_data.get('top_k')
        if value is None:
            return 3
        return value

    def clean(self):
        cleaned = super().clean()
        if self.user and not self.fields['model_id'].choices:
            raise forms.ValidationError('Chưa có mô hình sẵn sàng để phân loại. Hãy huấn luyện trước.')
        return cleaned


class HistoryFilterForm(forms.Form):
    """Form lọc lịch sử phân loại — submit bằng GET."""

    q = forms.CharField(
        required=False,
        label='Tìm kiếm',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Nhãn, tên ảnh, tên model...',
        }),
    )
    model_id = forms.ChoiceField(
        required=False,
        label='Mô hình',
        choices=[],
        widget=forms.Select(attrs={'class': 'aurora-input'}),
    )
    user_id = forms.ChoiceField(
        required=False,
        label='Người dùng',
        choices=[],
        widget=forms.Select(attrs={'class': 'aurora-input'}),
    )
    date_from = forms.DateField(
        required=False,
        label='Từ ngày',
        widget=forms.DateInput(attrs={'class': 'aurora-input', 'type': 'date'}),
    )
    date_to = forms.DateField(
        required=False,
        label='Đến ngày',
        widget=forms.DateInput(attrs={'class': 'aurora-input', 'type': 'date'}),
    )

    def __init__(self, *args, user: User | None = None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        from apps.predictions.services.prediction_history_service import PredictionHistoryService

        model_choices = [('', '— Tất cả model —')]
        if user:
            model_choices += [
                (str(mid), name)
                for mid, name in PredictionHistoryService.get_model_filter_options(user)
            ]
        self.fields['model_id'].choices = model_choices

        if user and user.is_admin:
            user_choices = [('', '— Tất cả người dùng —')]
            user_choices += [
                (str(uid), name)
                for uid, name in PredictionHistoryService.get_user_filter_options(user)
            ]
            self.fields['user_id'].choices = user_choices
        else:
            del self.fields['user_id']
