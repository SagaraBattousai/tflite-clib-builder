"""LinuxBuilder Module"""
# from typing import overload #<- not until 3.12
from tflite_clib_builder.builders.abstract_builder import AbstractBuilder


# Could have unix abstract parent since Android an Linux so similar!
class LinuxBuilder(AbstractBuilder):
    """Linux Builder Class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def platform() -> str:
        return "linux"

    @classmethod
    def shared_library_prefix(cls) -> str:
        return "lib"

    @classmethod
    def shared_library_extension(cls) -> str:
        return ".so"
