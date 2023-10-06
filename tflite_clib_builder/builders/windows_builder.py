"""WindowsBuilder Module"""
# from typing import overload #<- not until 3.12

import shutil
from tflite_clib_builder.builders.abstract_builder import AbstractBuilder


class WindowsBuilder(AbstractBuilder):
    """Windows Builder Class"""

    LINK_LIB_EXT = ".lib"  # Could also be .dll.a

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def platform() -> str:
        return "windows"

    @classmethod
    def shared_library_extension(cls) -> str:
        return ".dll"

    # override
    def output_library_dir(self) -> str:
        return f"{self.output_build_dir()}/Debug"

    # override
    def cmake_flags(self) -> list[str]:
        flags = super().cmake_flags()
        flags.extend(
            ["-DTFLITE_ENABLE_MMAP=OFF", "-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON"]
        )

        return flags

    # override
    def build(self):
        super().build()

        lib_out = self.get_library_dest()
        if self.dry_run:
            # May need to check .dll.a if .lib is not found.
            print(
                f"copying {self.output_build_dir()}/"
                f"{self.LIBRARY_BASE_NAME}{self.LINK_LIB_EXT} to {lib_out}",
            )
        else:
            # May need to check .dll.a if .lib is not found.
            shutil.copy2(f"{self.LIBRARY_BASE_NAME}{self.LINK_LIB_EXT}", lib_out)
