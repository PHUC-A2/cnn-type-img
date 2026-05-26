"""Render biểu đồ Matplotlib/Seaborn — embed base64 vào UI."""

import base64
import io
from typing import Optional


class ChartImageService:
    """Tạo ảnh PNG từ confusion matrix."""

    @staticmethod
    def render_confusion_matrix(matrix: list[list[int]], labels: list[str]) -> Optional[str]:
        """Vẽ heatmap confusion matrix — trả về chuỗi base64 PNG."""
        if not matrix or not labels:
            return None

        try:
            import matplotlib

            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            import seaborn as sns
        except ImportError:
            return None

        data = np.array(matrix, dtype=int)
        fig, ax = plt.subplots(figsize=(max(5, len(labels) * 0.9), max(4.5, len(labels) * 0.8)))
        sns.heatmap(
            data,
            annot=True,
            fmt='d',
            cmap='Purples',
            xticklabels=labels,
            yticklabels=labels,
            ax=ax,
            cbar_kws={'shrink': 0.85},
        )
        ax.set_xlabel('Dự đoán', fontsize=10)
        ax.set_ylabel('Thực tế', fontsize=10)
        ax.set_title('Confusion Matrix', fontsize=11, pad=12)
        plt.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=120, bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('ascii')
