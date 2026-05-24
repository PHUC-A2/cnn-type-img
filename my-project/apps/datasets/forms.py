"""Form upload bộ dữ liệu."""

from django import forms


class DatasetUploadForm(forms.Form):
    """Form tải lên dataset ZIP — validation backend tiếng Việt."""

    dataset_name = forms.CharField(
        max_length=100,
        label='Tên bộ dữ liệu',
        widget=forms.TextInput(attrs={
            'class': 'aurora-input',
            'placeholder': 'Ví dụ: Animals-10',
            'data-field': 'dataset_name',
        }),
    )
    description = forms.CharField(
        required=False,
        label='Mô tả',
        widget=forms.Textarea(attrs={
            'class': 'aurora-input aurora-textarea',
            'placeholder': 'Mô tả ngắn về bộ dữ liệu (tùy chọn)',
            'rows': 3,
            'data-field': 'description',
        }),
    )
    zip_file = forms.FileField(
        label='File ZIP',
        widget=forms.ClearableFileInput(attrs={
            'class': 'aurora-file hidden',
            'data-field': 'zip_file',
            'accept': '',
        }),
    )

    def clean_dataset_name(self):
        name = self.cleaned_data['dataset_name'].strip()
        if len(name) < 3:
            raise forms.ValidationError('Tên bộ dữ liệu phải có ít nhất 3 ký tự.')
        return name
