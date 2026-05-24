/** Khởi tạo Lucide icons sau mỗi lần load trang / HTMX swap */
document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide) {
        lucide.createIcons();
    }
});

document.body.addEventListener('htmx:afterSwap', () => {
    if (window.lucide) {
        lucide.createIcons();
    }
    if (window.initTrainingCharts) {
        window.initTrainingCharts();
    }
});
