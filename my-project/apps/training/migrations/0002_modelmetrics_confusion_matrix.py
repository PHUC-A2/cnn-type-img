"""Thêm confusion matrix vào model_metrics."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelmetrics',
            name='class_labels_json',
            field=models.JSONField(blank=True, null=True, verbose_name='Nhãn class'),
        ),
        migrations.AddField(
            model_name='modelmetrics',
            name='confusion_matrix_json',
            field=models.JSONField(blank=True, null=True, verbose_name='Confusion matrix'),
        ),
    ]
