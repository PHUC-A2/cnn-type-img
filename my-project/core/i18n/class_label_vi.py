"""Ánh xạ tên class dataset → nhãn hiển thị tiếng Việt."""

import re
import unicodedata

_CLASS_LABEL_VI: dict[str, str] = {
    'dog': 'Con chó',
    'dogs': 'Con chó',
    'puppy': 'Con chó con',
    'cat': 'Con mèo',
    'cats': 'Con mèo',
    'kitten': 'Con mèo con',
    'bird': 'Con chim',
    'birds': 'Con chim',
    'chim': 'Con chim',
    'cho': 'Con chó',
    'chó': 'Con chó',
    'con cho': 'Con chó',
    'meo': 'Con mèo',
    'mèo': 'Con mèo',
    'con meo': 'Con mèo',
    'con mèo': 'Con mèo',
    'person': 'Con người',
    'people': 'Con người',
    'human': 'Con người',
    'humans': 'Con người',
    'nguoi': 'Con người',
    'người': 'Con người',
    'con nguoi': 'Con người',
    'con người': 'Con người',
    'man': 'Người đàn ông',
    'woman': 'Người phụ nữ',
    'boy': 'Bé trai',
    'girl': 'Bé gái',
    'horse': 'Con ngựa',
    'ngua': 'Con ngựa',
    'cow': 'Con bò',
    'bo': 'Con bò',
    'pig': 'Con lợn',
    'lon': 'Con lợn',
    'sheep': 'Con cừu',
    'fish': 'Con cá',
    'ca': 'Con cá',
    'cá': 'Con cá',
    'rabbit': 'Con thỏ',
    'tho': 'Con thỏ',
    'thỏ': 'Con thỏ',
    'duck': 'Con vịt',
    'vit': 'Con vịt',
    'vịt': 'Con vịt',
    'chicken': 'Con gà',
    'ga': 'Con gà',
    'gà': 'Con gà',
    'car': 'Xe ô tô',
    'xe': 'Xe ô tô',
    'motorbike': 'Xe máy',
    'xe may': 'Xe máy',
    'flower': 'Hoa',
    'hoa': 'Hoa',
    'tree': 'Cây',
    'cay': 'Cây',
    'fruit': 'Trái cây',
    'apple': 'Quả táo',
    'banana': 'Quả chuối',
    'animal': 'Động vật',
    'animals': 'Động vật',
    'dong vat': 'Động vật',
    'động vật': 'Động vật',
    'pet': 'Thú cưng',
    'thu cung': 'Thú cưng',
}

_ANIMAL_KEYWORDS = (
    'dog', 'cat', 'bird', 'chim', 'cho', 'chó', 'meo', 'mèo', 'animal', 'pet',
    'dong vat', 'động vật', 'thu cung', 'thú cưng', 'horse', 'cow', 'fish', 'ca', 'cá',
    'pig', 'lon', 'lợn', 'rabbit', 'tho', 'thỏ', 'duck', 'vit', 'vịt', 'chicken', 'ga', 'gà',
    'ngua', 'ngựa', 'bo', 'bò', 'puppy', 'kitten',
)
_PERSON_KEYWORDS = (
    'person', 'human', 'people', 'nguoi', 'người', 'man', 'woman', 'face',
    'khuon mat', 'khuôn mặt', 'boy', 'girl', 'con nguoi', 'con người',
)
_VEHICLE_KEYWORDS = ('car', 'xe', 'motorbike', 'xe may', 'xe máy', 'truck', 'bus')
_PLANT_KEYWORDS = ('flower', 'hoa', 'tree', 'cay', 'cây', 'plant', 'thuc vat', 'thực vật')

_VIETNAMESE_CHAR_PATTERN = re.compile(
    r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
    re.IGNORECASE,
)


def normalize_class_key(class_name: str) -> str:
    return class_name.strip().lower().replace('_', ' ').replace('-', ' ')


def strip_vietnamese_accents(text: str) -> str:
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')


def is_vietnamese_text(text: str) -> bool:
    return bool(_VIETNAMESE_CHAR_PATTERN.search(text))


def suggest_vietnamese_label(class_name: str) -> str:
    """Gợi ý nhãn tiếng Việt từ tên class/thư mục dataset."""
    raw = class_name.strip()
    if not raw:
        return raw

    if is_vietnamese_text(raw):
        return raw

    key = normalize_class_key(raw)
    if key in _CLASS_LABEL_VI:
        return _CLASS_LABEL_VI[key]

    key_no_accent = strip_vietnamese_accents(key)
    if key_no_accent in _CLASS_LABEL_VI:
        return _CLASS_LABEL_VI[key_no_accent]

    for map_key, label in _CLASS_LABEL_VI.items():
        if strip_vietnamese_accents(map_key) == key_no_accent:
            return label

    return raw.replace('_', ' ').replace('-', ' ').title()


def infer_object_category(class_name: str, display_label: str | None = None) -> str:
    combined = f'{class_name} {display_label or ""}'.lower()
    combined_no_accent = strip_vietnamese_accents(combined)

    def _match(keywords: tuple[str, ...]) -> bool:
        return any(
            kw in combined or strip_vietnamese_accents(kw) in combined_no_accent
            for kw in keywords
        )

    if _match(_PERSON_KEYWORDS):
        return 'Con người'
    if _match(_ANIMAL_KEYWORDS):
        return 'Động vật'
    if _match(_VEHICLE_KEYWORDS):
        return 'Phương tiện'
    if _match(_PLANT_KEYWORDS):
        return 'Thực vật'
    return 'Đối tượng trong dataset'


def build_label_map(class_names: list[str]) -> dict[str, str]:
    return {name: suggest_vietnamese_label(name) for name in class_names}
