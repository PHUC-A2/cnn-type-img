"""Views dashboard phân tích AI — Phase 7."""

import json

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.analytics.forms import AnalyticsFilterForm
from apps.analytics.services.analytics_dashboard_service import AnalyticsDashboardService
from core.permissions.decorators import login_required


@login_required
def analytics_view(request: HttpRequest) -> HttpResponse:
    """Dashboard thống kê AI — widget + biểu đồ."""
    job_id = AnalyticsDashboardService.parse_job_id(request.GET.get('job_id'))
    dashboard = AnalyticsDashboardService.build_dashboard(request.user, job_id=job_id)
    filter_form = AnalyticsFilterForm(
        request.GET or None,
        user=request.user,
        selected_job_id=dashboard.selected_job_id,
        job_options=dashboard.job_options,
    )

    context = {
        'page_title': 'Phân tích AI',
        'active_nav': 'analytics',
        'dashboard': dashboard,
        'filter_form': filter_form,
        'model_comparison_labels_json': json.dumps([row.model_name for row in dashboard.model_comparison]),
        'model_comparison_accuracy_json': json.dumps([row.accuracy for row in dashboard.model_comparison]),
        'model_comparison_f1_json': json.dumps([row.f1 for row in dashboard.model_comparison]),
        'dataset_labels_json': json.dumps([row.label for row in dashboard.dataset_distribution]),
        'dataset_counts_json': json.dumps([row.count for row in dashboard.dataset_distribution]),
        'prediction_labels_json': json.dumps([row.label for row in dashboard.prediction_distribution]),
        'prediction_counts_json': json.dumps([row.count for row in dashboard.prediction_distribution]),
        'chart_labels_json': json.dumps(dashboard.training_chart.labels),
        'chart_train_acc_json': json.dumps(dashboard.training_chart.train_acc),
        'chart_val_acc_json': json.dumps(dashboard.training_chart.val_acc),
        'chart_train_loss_json': json.dumps(dashboard.training_chart.train_loss),
        'chart_val_loss_json': json.dumps(dashboard.training_chart.val_loss),
    }
    return render(request, 'analytics/index.html', context)
