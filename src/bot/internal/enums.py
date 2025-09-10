from enum import IntEnum, auto


class ModelMenuBtns(IntEnum):
    UPLOAD_NEW_PHOTO = auto()
    KEEP_PHOTO = auto()
    CONFIRM_KEEP_PHOTO = auto()
    REQUIREMENTS_BEFORE_PAYMENT = auto()
    REQUIREMENTS_AFTER_PAYMENT = auto()
    DETAILS = auto()


class PhotoMenuBtns(IntEnum):
    ACCEPT = auto()
    DECLINE = auto()
