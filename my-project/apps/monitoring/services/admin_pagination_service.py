"""Phân trang danh sách admin — tái sử dụng cho mọi bảng."""

from dataclasses import dataclass

from django.core.paginator import Paginator


@dataclass
class AdminPageResult:
    """Kết quả phân trang admin."""

    items: list
    page: int
    total_pages: int
    total_count: int
    has_next: bool
    has_prev: bool


class AdminPaginationService:
    """Helper phân trang queryset admin."""

    PAGE_SIZE = 12

    @staticmethod
    def paginate(qs, page: int = 1, page_size: int | None = None) -> AdminPageResult:
        size = page_size or AdminPaginationService.PAGE_SIZE
        paginator = Paginator(qs, size)
        page = max(1, min(page, paginator.num_pages or 1))
        page_obj = paginator.get_page(page)
        return AdminPageResult(
            items=list(page_obj.object_list),
            page=page_obj.number,
            total_pages=paginator.num_pages,
            total_count=paginator.count,
            has_next=page_obj.has_next(),
            has_prev=page_obj.has_previous(),
        )
