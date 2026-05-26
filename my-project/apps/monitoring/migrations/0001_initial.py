"""Migration khởi tạo bảng logging Phase 9."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('info', 'Thông tin'), ('warning', 'Cảnh báo'), ('error', 'Lỗi')], default='info', max_length=20, verbose_name='Mức độ')),
                ('source', models.CharField(max_length=100, verbose_name='Nguồn')),
                ('message', models.TextField(verbose_name='Nội dung')),
                ('stack_trace', models.TextField(blank=True, null=True, verbose_name='Stack trace')),
                ('context_json', models.JSONField(blank=True, null=True, verbose_name='Context')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')),
            ],
            options={
                'verbose_name': 'Log hệ thống',
                'verbose_name_plural': 'Log hệ thống',
                'db_table': 'system_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ApiRequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(max_length=10, verbose_name='Method')),
                ('path', models.CharField(max_length=500, verbose_name='Đường dẫn')),
                ('endpoint', models.CharField(blank=True, max_length=200, null=True, verbose_name='Endpoint')),
                ('status_code', models.IntegerField(verbose_name='Status')),
                ('execution_time_ms', models.FloatField(verbose_name='Thời gian (ms)')),
                ('ip_address', models.CharField(blank=True, max_length=45, null=True, verbose_name='IP')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')),
                ('user', models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='api_request_logs', to='authentication.user', verbose_name='Người dùng')),
            ],
            options={
                'verbose_name': 'Log request',
                'verbose_name_plural': 'Log request',
                'db_table': 'api_request_logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
