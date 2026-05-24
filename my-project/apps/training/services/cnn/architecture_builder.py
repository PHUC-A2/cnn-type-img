"""Xây dựng kiến trúc CNN cơ bản — Conv2D → Pool → Dropout → Dense → Softmax."""

from typing import Tuple


def build_cnn_model(input_shape: Tuple[int, int, int], num_classes: int):
    """Tạo model Keras Sequential."""
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import (
        Conv2D,
        Dense,
        Dropout,
        Flatten,
        MaxPooling2D,
    )

    model = Sequential(name='cnn_basic')
    model.add(Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(128, (3, 3), activation='relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))
    return model
