"""LinuxBuilder Module"""
# from typing import overload #<- not until 3.12
import shutil
from tflite_clib_builder.builders.abstract_builder import AbstractBuilder


# Could have unix abstract parent since Android an Linux so similar!
class LinuxBuilder(AbstractBuilder):
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

    # override
    def build(self):
        super().build()

        lib_out = self.get_library_dest()
        if self.dry_run:
            print(
                f"copying {self.output_library_dir()}/{self.library_name()}"
                f"to {lib_out}",
            )
        else:
            shutil.copy2(f"{self.output_library_dir()}/{self.library_name()}", lib_out)
