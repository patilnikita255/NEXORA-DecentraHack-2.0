"""
M03 training augmentation configuration.

These augmentations are intended for person detection
under CCTV conditions such as:

- Low light
- Blur
- Different camera angles
- Different scales
- Partial visibility

Actual augmentation values should be validated
experimentally during model training.
"""


AUGMENTATION_CONFIG = {
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,

    "degrees": 5.0,
    "translate": 0.1,
    "scale": 0.5,
    "shear": 2.0,
    "perspective": 0.0005,

    "flipud": 0.0,
    "fliplr": 0.5,

    "mosaic": 1.0,
    "mixup": 0.0,

    "close_mosaic": 10,
}


def get_augmentation_config():
    """
    Return a copy of the augmentation configuration.
    """

    return AUGMENTATION_CONFIG.copy()


if __name__ == "__main__":
    print("M03 augmentation configuration:")

    for key, value in AUGMENTATION_CONFIG.items():
        print(f"{key}: {value}")