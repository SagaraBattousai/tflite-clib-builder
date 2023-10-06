"""AndroidBuilder Module"""
# from typing import overload #<- not until 3.12
import os
from tflite_clib_builder.builders.abstract_builder import AbstractBuilder


class AndroidBuilder(AbstractBuilder):
    """Android Builder Class"""

    NDK_VERSION_SEP = "."

    def __init__(
        self,
        android_stl: str = "c++_shared",
        android_abi: str | None = "arm64-v8a",  # None gets passed in from argparse
        android_platform: str | None = None,
        android_sdk_path: str | None = None,
        ndk_version: str | None = None,
        generator: str | None = "Ninja",  # None gets passed in from argparse
        **kwargs,
    ):
        if generator is None:
            generator = "Ninja"
        super().__init__(generator=generator, **kwargs)
        self.android_stl = android_stl
        self.android_abi = android_abi if android_abi else "arm64-v8a"
        self.android_platform = android_platform
        self.android_sdk_path = android_sdk_path
        self.ndk_version = ndk_version

    @staticmethod
    def platform() -> str:
        return "android"

    @classmethod
    def shared_library_prefix(cls) -> str:
        return "lib"

    @classmethod
    def shared_library_extension(cls) -> str:
        return ".so"

    # override
    def build_dir(self) -> str:
        # root_dir = f"{super().build_dir()}/{self.android_abi}"
        return f"{super().build_dir()}/{self.android_abi}"

    def library_output_dir(self) -> str:
        base_dir = f"{self.LIBRARY_BASE_NAME}/lib/{self.platform()}/{self.android_abi}"

        root_dir = (
            base_dir
            if not self.android_platform
            else f"{base_dir}/{self.android_platform}"
        )

        return (
            root_dir
            if not self.build_root
            else f"{self.build_root}/{root_dir}/{self.build_type}"
        )

    # override
    def cmake_flags(self) -> list[str]:
        flags = super().cmake_flags()
        flags.append("-DANDROID_STL=" + self.android_stl)
        flags.append("-DANDROID_ABI=" + self.android_abi)

        if self.android_platform:
            flags.append("-DANDROID_PLATFORM=" + self.android_platform)

        # Could make constructor arg required
        if not self.android_sdk_path:
            raise RuntimeError(
                "When configuring for android, android_sdk_path must be set."
            )

        # Could also move to constructor (especially if above comment is applied)
        ndk_path = f"{self.android_sdk_path}/ndk"

        if not self.ndk_version:
            ndk_version_list = os.listdir(ndk_path)

            if len(ndk_version_list) == 0:
                raise RuntimeError(
                    "When configuring for android, either ndk_version must be set"
                    " or a directory with an ndk version string must exist in the"
                    f" ndk subdirectory of android_skd_path: {ndk_path}."
                )

            if len(ndk_version_list) == 1:
                self.ndk_version = ndk_version_list[0]
            else:
                self.ndk_version = self.NDK_VERSION_SEP.join(
                    max(
                        version_dir.split(self.NDK_VERSION_SEP)
                        for version_dir in ndk_version_list
                    )
                )

        ndk_version_path = f"{ndk_path}/{self.ndk_version}"
        flags.append("-DANDROID_NDK=" + ndk_version_path)
        flags.append(
            f"-DCMAKE_TOOLCHAIN_FILE={ndk_version_path}/build/cmake/"
            "android.toolchain.cmake"
        )

        return flags
