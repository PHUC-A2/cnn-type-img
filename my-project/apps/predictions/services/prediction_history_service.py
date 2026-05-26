"""Service lịch sử phân loại — filter, search, pagination."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.core.paginator import Paginator
from django.db.models import Q

from apps.authentication.models import User
from apps.models_ai.models import CnnModel
from apps.predictions.models import Prediction


@dataclass
class HistoryFilters:
    """Bộ lọc trang lịch sử."""

    q: str = ''
    model_id: Optional[int] = None
    user_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


@dataclass
class HistoryPageResult:
    """Kết quả phân trang lịch sử."""

    items: list
    page: int
    total_pages: int
    total_count: int
    has_next: bool
    has_prev: bool


class PredictionHistoryService:
    """Truy vấn lịch sử predictions với filter."""

    PAGE_SIZE = 10

    @staticmethod
    def _base_queryset(user: User):
        """Query cơ sở — admin xem tất cả, user thường chỉ của mình."""
        qs = Prediction.objects.select_related('model', 'predicted_by').order_by('-created_at')
        if not user.is_admin:
            qs = qs.filter(predicted_by_id=user.id)
        return qs

    @staticmethod
    def list_history(user: User, filters: HistoryFilters, page: int = 1) -> HistoryPageResult:
        """Lọc và phân trang danh sách prediction."""
        qs = PredictionHistoryService._base_queryset(user)

        if user.is_admin and filters.user_id:
            qs = qs.filter(predicted_by_id=filters.user_id)

        if filters.model_id:
            qs = qs.filter(model_id=filters.model_id)

        if filters.date_from:
            qs = qs.filter(created_at__date__gte=filters.date_from)

        if filters.date_to:
            qs = qs.filter(created_at__date__lte=filters.date_to)

        if filters.q:
            keyword = filters.q.strip()
            qs = qs.filter(
                Q(predicted_class__icontains=keyword)
                | Q(image_name__icontains=keyword)
                | Q(model__model_name__icontains=keyword)
            )

        paginator = Paginator(qs, PredictionHistoryService.PAGE_SIZE)
        page = max(1, min(page, paginator.num_pages or 1))
        page_obj = paginator.get_page(page)

        return HistoryPageResult(
            items=list(page_obj.object_list),
            page=page_obj.number,
            total_pages=paginator.num_pages,
            total_count=paginator.count,
            has_next=page_obj.has_next(),
            has_prev=page_obj.has_previous(),
        )

    @staticmethod
    def get_model_filter_options(user: User) -> list[tuple[int, str]]:
        """Danh sách model xuất hiện trong lịch sử để filter."""
        model_ids = (
            PredictionHistoryService._base_queryset(user)
            .values_list('model_id', flat=True)
            .distinct()
        )
        models = CnnModel.objects.filter(id__in=model_ids).order_by('model_name')
        return [(m.id, m.model_name) for m in models]

    @staticmethod
    def get_user_filter_options(user: User) -> list[tuple[int, str]]:
        """Danh sách user cho admin filter."""
        if not user.is_admin:
            return []
        user_ids = Prediction.objects.values_list('predicted_by_id', flat=True).distinct()
        users = User.objects.filter(id__in=user_ids).order_by('username')
        return [(u.id, u.get_display_name()) for u in users]

    @staticmethod
    def parse_filters(raw: dict, user: User) -> HistoryFilters:
        """Parse query string GET thành HistoryFilters."""
        q = (raw.get('q') or '').strip()

        model_id = None
        if raw.get('model_id'):
            try:
                model_id = int(raw.get('model_id'))
            except (TypeError, ValueError):
                model_id = None

        user_id = None
        if user.is_admin and raw.get('user_id'):
            try:
                user_id = int(raw.get('user_id'))
            except (TypeError, ValueError):
                user_id = None

        date_from = PredictionHistoryService._parse_date(raw.get('date_from'))
        date_to = PredictionHistoryService._parse_date(raw.get('date_to'))

        return HistoryFilters(
            q=q,
            model_id=model_id,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )

    @staticmethod
    def _parse_date(value) -> Optional[date]:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None
