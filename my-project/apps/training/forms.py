"""Form cấu hình huấn luyện CNN."""

from django import forms

from apps.datasets.repositories.dataset_repository import DatasetRepository


class TrainingConfigForm(forms.Form):
    """Form chọn dataset + hyperparameters — validation backend."""

    model_name = forms.CharField(
        max_length=100,
        label='Tên mô hình',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Ví dụ: CNN-Cho-Meo-v1',
            'data-field': 'model_name',
        }),
    )
    dataset_id = forms.ChoiceField(
        label='Bộ dữ liệu',
        widget=forms.Select(attrs={
            'class': 'aurora-input',
            'data-field': 'dataset_id',
        }),
    )
    description = forms.CharField(
        required=False,
        label='Mô tả',
        widget=forms.Textarea(attrs={
            'class': 'aurora-input aurora-textarea',
            'rows': 2,
            'data-field': 'description',
        }),
    )
    input_width = forms.IntegerField(
        initial=128,
        label='Chiều rộng ảnh (px)',
        widget=forms.NumberInput(attrs={'class': 'aurora-input', 'data-field': 'input_width'}),
    )
    input_height = forms.IntegerField(
        initial=128,
        label='Chiều cao ảnh (px)',
        widget=forms.NumberInput(attrs={'class': 'aurora-input', 'data-field': 'input_height'}),
    )
    epochs = forms.IntegerField(
        initial=10,
        label='Số epoch',
        widget=forms.NumberInput(attrs={'class': 'aurora-input', 'data-field': 'epochs'}),
    )
    batch_size = forms.IntegerField(
        initial=16,
        label='Batch size',
        widget=forms.NumberInput(attrs={'class': 'aurora-input', 'data-field': 'batch_size'}),
    )
    learning_rate = forms.CharField(
        initial='0.001',
        label='Learning rate',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'inputmode': 'decimal',
            'placeholder': '0.001',
            'data-field': 'learning_rate',
        }),
    )
    optimizer = forms.ChoiceField(
        choices=[
            ('adam', 'Adam'),
            ('sgd', 'SGD'),
            ('rmsprop', 'RMSprop'),
        ],
        initial='adam',
        label='Optimizer',
        widget=forms.Select(attrs={'class': 'aurora-input', 'data-field': 'optimizer'}),
    )
    loss_function = forms.ChoiceField(
        choices=[('categorical_crossentropy', 'Categorical Crossentropy')],
        initial='categorical_crossentropy',
        label='Hàm loss',
        widget=forms.Select(attrs={'class': 'aurora-input', 'data-field': 'loss_function'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        if user:
            for ds in DatasetRepository.list_for_user(user):
                choices.append((str(ds.id), f'{ds.dataset_name} ({ds.total_images} ảnh, {ds.total_classes} class)'))
        self.fields['dataset_id'].choices = [('', '-- Chọn bộ dữ liệu --')] + choices

    def clean_model_name(self):
        name = self.cleaned_data['model_name'].strip()
        if len(name) < 3:
            raise forms.ValidationError('Tên mô hình phải có ít nhất 3 ký tự.')
        return name

    def clean_dataset_id(self):
        value = self.cleaned_data['dataset_id']
        if not value:
            raise forms.ValidationError('Vui lòng chọn bộ dữ liệu.')
        return int(value)

    def clean_epochs(self):
        value = self.cleaned_data['epochs']
        if value < 1 or value > 100:
            raise forms.ValidationError('Số epoch phải từ 1 đến 100.')
        return value

    def clean_batch_size(self):
        value = self.cleaned_data['batch_size']
        if value < 4 or value > 128:
            raise forms.ValidationError('Batch size phải từ 4 đến 128.')
        return value

    def clean_input_width(self):
        value = self.cleaned_data['input_width']
        if value < 32 or value > 512:
            raise forms.ValidationError('Chiều rộng phải từ 32 đến 512 px.')
        return value

    def clean_input_height(self):
        value = self.cleaned_data['input_height']
        if value < 32 or value > 512:
            raise forms.ValidationError('Chiều cao phải từ 32 đến 512 px.')
        return value

    def clean_learning_rate(self):
        raw = self.cleaned_data['learning_rate'].strip().replace(',', '.')
        if not raw:
            raise forms.ValidationError('Vui lòng nhập learning rate.')
        try:
            value = float(raw)
        except ValueError as exc:
            raise forms.ValidationError('Learning rate không hợp lệ. Dùng dấu chấm, ví dụ: 0.001.') from exc
        if value <= 0 or value > 1:
            raise forms.ValidationError('Learning rate phải lớn hơn 0 và nhỏ hơn 1.')
        return value
