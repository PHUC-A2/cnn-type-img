"""Test ánh xạ nhãn class sang tiếng Việt."""

from django.test import TestCase

from core.i18n.class_label_vi import (
    infer_object_category,
    is_vietnamese_text,
    suggest_vietnamese_label,
)


class ClassLabelViTest(TestCase):
    """Test module core.i18n.class_label_vi."""

    def test_english_slug_to_vietnamese(self):
        self.assertEqual(suggest_vietnamese_label('dog'), 'Con chó')
        self.assertEqual(suggest_vietnamese_label('cat'), 'Con mèo')
        self.assertEqual(suggest_vietnamese_label('person'), 'Con người')

    def test_vietnamese_folder_name_kept(self):
        self.assertEqual(suggest_vietnamese_label('Con mèo'), 'Con mèo')
        self.assertTrue(is_vietnamese_text('Con chó'))

    def test_no_accent_slug(self):
        self.assertEqual(suggest_vietnamese_label('cho'), 'Con chó')
        self.assertEqual(suggest_vietnamese_label('meo'), 'Con mèo')

    def test_infer_category(self):
        self.assertEqual(infer_object_category('dog', 'Con chó'), 'Động vật')
        self.assertEqual(infer_object_category('person'), 'Con người')
        self.assertEqual(infer_object_category('car'), 'Phương tiện')
