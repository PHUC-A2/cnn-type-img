/** Sidebar responsive + Lucide icons — Aurora AI Theme */
document.addEventListener('alpine:init', () => {
    Alpine.data('auroraSidebar', () => ({
        mobileOpen: false,
        tabletPinned: false,
        tabletHover: false,
        viewport: 'desktop',

        init() {
            this.tabletPinned = localStorage.getItem('aurora_sidebar_tablet') === '1';

            const syncViewport = () => {
                const w = window.innerWidth;
                if (w >= 1024) {
                    this.viewport = 'desktop';
                    this.mobileOpen = false;
                } else if (w >= 768) {
                    this.viewport = 'tablet';
                    this.mobileOpen = false;
                } else {
                    this.viewport = 'mobile';
                }
            };

            syncViewport();
            window.addEventListener('resize', syncViewport);
        },

        toggleMobile() {
            this.mobileOpen = !this.mobileOpen;
            this._syncBodyScroll();
            this.$nextTick(() => {
                if (window.lucide) lucide.createIcons();
            });
        },

        closeMobile() {
            this.mobileOpen = false;
            this._syncBodyScroll();
        },

        toggleTablet() {
            this.tabletPinned = !this.tabletPinned;
            localStorage.setItem('aurora_sidebar_tablet', this.tabletPinned ? '1' : '0');
            this.$nextTick(() => {
                if (window.lucide) lucide.createIcons();
            });
        },

        onTabletEnter() {
            if (this.viewport === 'tablet' && !this.tabletPinned) {
                this.tabletHover = true;
            }
        },

        onTabletLeave() {
            this.tabletHover = false;
        },

        isIconOnly() {
            return this.viewport === 'tablet' && !this.tabletPinned && !this.tabletHover;
        },

        isTabletExpanded() {
            return this.viewport === 'tablet' && (this.tabletPinned || this.tabletHover);
        },

        sidebarClass() {
            if (this.viewport === 'mobile') {
                return `aurora-sidebar aurora-sidebar-mobile fixed flex flex-col z-50 transition-all duration-[220ms] ease-out inset-y-0 left-0 w-[260px] rounded-r-2xl ${
                    this.mobileOpen ? 'translate-x-0' : '-translate-x-full'
                }`;
            }
            if (this.viewport === 'tablet') {
                return `aurora-sidebar aurora-sidebar-tablet fixed flex flex-col z-50 transition-all duration-[220ms] ease-out left-3 top-3 bottom-3 ${
                    this.isTabletExpanded() ? 'w-[260px]' : 'w-[72px] aurora-sidebar-collapsed'
                }`;
            }
            return 'aurora-sidebar aurora-sidebar-desktop fixed inset-y-0 left-0 flex flex-col z-30 w-[260px] h-screen';
        },

        spacerClass() {
            if (this.viewport === 'desktop') return 'block w-[260px] flex-shrink-0';
            if (this.viewport === 'mobile') return 'hidden';
            return this.isTabletExpanded()
                ? 'block w-[276px] flex-shrink-0'
                : 'block w-[88px] flex-shrink-0';
        },

        _syncBodyScroll() {
            const lock = this.mobileOpen && this.viewport === 'mobile';
            document.body.classList.toggle('overflow-hidden', lock);
        },
    }));
});

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
    if (window.initAnalyticsCharts) {
        window.initAnalyticsCharts();
    }
});
