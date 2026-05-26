"""Form lọc dashboard phân tích — chọn job huấn luyện."""

from django import forms

from apps.authentication.models import User


class AnalyticsFilterForm(forms.Form):
    """Chọn job để xem biểu đồ training + confusion matrix."""

    job_id = forms.ChoiceField(
        required=False,
        label='Job huấn luyện',
        choices=[],
        widget=forms.Select(attrs={
            'class': 'aurora-input',
            'onchange': 'this.form.submit()',
        }),
    )

    def __init__(self, *args, user: User | None = None, selected_job_id=None, job_options=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        choices = [('', '— Chọn job hoàn thành —')]
        if job_options:
            choices += [(str(opt.job_id), opt.label) for opt in job_options]

        self.fields['job_id'].choices = choices
        if selected_job_id:
            self.fields['job_id'].initial = str(selected_job_id)
