"""AbstractBuilder Module"""
import os
import shutil
import subprocess

# import os.path
from abc import ABCMeta, abstractmethod


class AbstractBuilder(metaclass=ABCMeta):
    """AbstractBuilder Class"""

    # I hate the hardcodyness of this line (well the .. parts)
    TENSORFLOW_LITE_ROOT = os.path.abspath(
        f"{os.path.dirname(__spec__.origin)}"  # type: ignore[name-defined]
        "/../../tensorflow_src/tensorflow/lite"
    )

    TENSORFLOW_LITE_C_CMAKE_PATH = f"{TENSORFLOW_LITE_ROOT}/c"

    LIBRARY_BASE_NAME = "tensorflowlite_c"
    BUILD_OUTPUT_DIR_FILENAME = "c_lib_output_dir.txt"
    HEADER_INCLUDE_BASE_PATH = "include/tensorflow/lite"
    # HEADER_SOURCE_ROOT = "../tensorflow_src/tensorflow/lite"
    HEADER_SUFFIX = ".h"

    def __init__(
        self,
        build_type: str = "Release",
        build_root: str | None = None,
        generator: str | None = None,
        dry_run: bool = False,
        **_kwargs,
    ):
        self.build_type: str = build_type
        self.build_root = build_root
        self.generator = generator
        self.dry_run = dry_run

    @staticmethod
    @abstractmethod
    def platform() -> str:
        pass

    @classmethod
    def library_name(cls) -> str:
        return (
            cls.shared_library_prefix()
            + cls.LIBRARY_BASE_NAME
            + cls.shared_library_extension()
        )

    @classmethod
    def shared_library_prefix(cls) -> str:
        return ""

    @classmethod
    @abstractmethod
    def shared_library_extension(cls) -> str:
        pass

    def build_dir(self) -> str:
        # Separate for os's as they usually differ on the generator used
        # (will this cause issues with build types?).
        # No point having individual build dirs since that would be a huge waste
        base_dir = f"{self.platform()}/build"
        return base_dir if not self.build_root else f"{self.build_root}/{base_dir}"

    # Differes on windows so needed to be overloadable
    def library_build_dir(self) -> str:
        return self.build_dir()

    def library_output_dir(self) -> str:
        base_dir = f"{self.platform()}/{self.build_type}"
        return base_dir if not self.build_root else f"{self.build_root}/{base_dir}"

    def cmake_flags(self) -> list[str]:
        return ["-DABSL_PROPAGATE_CXX_STD=ON", f"-DCMAKE_BUILD_TYPE={self.build_type}"]

    # @staticmethod
    # def cmake_base_flags() -> list[str]:
    #     return ["-DABSL_PROPAGATE_CXX_STD=ON"]

    # This is actually an important function because we do not configure two
    # different directories for Release and Debug so this file will tell us which
    # has currently been configured.
    def get_library_dest(self) -> str:
        """Pre cond: configure has been called and build directory is not empty"""
        # lib_out = ""
        # TODO: Handle error file not exists etc
        with open(
            f"{self.build_dir()}/{self.BUILD_OUTPUT_DIR_FILENAME}",
            "r",
            encoding="utf-8",
        ) as f:
            # Safe enough as should be small unless someone maliciously adds to it.
            lib_out = f.read()
        return lib_out  # surprised this is safe

    def configure(self):
        flags = self.cmake_flags()

        if self.generator:
            flags.append(f"-G {self.generator}")

        flags.append(f"-B {self.build_dir()}")

        flags.append(f"-S {self.TENSORFLOW_LITE_C_CMAKE_PATH}")

        if self.dry_run:
            print("cmake", *flags, sep="\n\t")
            print(f"mkdir {self.build_dir()}")
            print(f"mkdir {self.library_output_dir()}")
            print(
                f"echo {self.library_output_dir()} >>"
                f" {self.build_dir()}/{self.BUILD_OUTPUT_DIR_FILENAME}"
            )
        else:
            os.makedirs(self.build_dir(), exist_ok=True)
            os.makedirs(self.library_output_dir(), exist_ok=True)
            with open(
                f"{self.build_dir()}/{self.BUILD_OUTPUT_DIR_FILENAME}",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(self.library_output_dir())
            subprocess.run(["cmake", *flags], check=False)

    # virtual
    def build(self):
        lib_out = self.get_library_dest()

        self.copy_headers_to_lib(lib_out)

        if self.dry_run:
            print("cmake", "--build", self.build_dir())
            print(
                f"copying {self.library_build_dir()}/{self.library_name()}"
                f" to {lib_out}",
            )
        else:
            subprocess.run(["cmake", "--build", self.build_dir()], check=True)
            shutil.copy2(f"{self.library_build_dir()}/{self.library_name()}", lib_out)

    def copy_headers_to_lib(self, lib_out: str):
        header_dst_root = f"{lib_out}/{self.HEADER_INCLUDE_BASE_PATH}"
        header_c_dst_root = f"{lib_out}/{self.HEADER_INCLUDE_BASE_PATH}/c"
        header_core_c_dst_root = f"{lib_out}/{self.HEADER_INCLUDE_BASE_PATH}/core/c"
        header_core_async_c_dst_root = (
            f"{lib_out}/{self.HEADER_INCLUDE_BASE_PATH}/core/async/c"
        )

        core_c_header_source = f"{self.TENSORFLOW_LITE_ROOT}/core/c"
        core_async_c_header_source = f"{self.TENSORFLOW_LITE_ROOT}/core/async/c"

        if self.dry_run:
            print("mkdir", header_c_dst_root)
            print("mkdir", header_core_c_dst_root)
            print("mkdir", header_core_async_c_dst_root)

            print(
                f"copying {os.path.relpath(self.TENSORFLOW_LITE_ROOT)}/builtin_ops.h to"
                f" {header_dst_root}"
            )

            print(
                f"copying {os.path.relpath(self.TENSORFLOW_LITE_ROOT)}/c/c_api.h"
                f" {header_c_dst_root}"
            )
            print(
                "copying"
                f" {os.path.relpath(self.TENSORFLOW_LITE_ROOT)}/c/c_api_experimental.h"
                f" to {header_c_dst_root}"
            )
            print(
                f"copying {os.path.relpath(self.TENSORFLOW_LITE_ROOT)}/c/c_api_types.h"
                f" to {header_c_dst_root}"
            )
            print(
                f"copying {os.path.relpath(self.TENSORFLOW_LITE_ROOT)}/c/common.h to"
                f" {header_c_dst_root}"
            )

            for file in os.listdir(core_c_header_source):
                if file.endswith(self.HEADER_SUFFIX):
                    print(
                        f"copying {os.path.relpath(core_c_header_source)}/{file} to"
                        f" {header_core_c_dst_root}/"
                    )

            for file in os.listdir(core_async_c_header_source):
                if file.endswith(self.HEADER_SUFFIX):
                    print(
                        "copying"
                        f" {os.path.relpath(core_async_c_header_source)}/{file} to"
                        f" {header_core_async_c_dst_root}/"
                    )
        else:
            os.makedirs(header_c_dst_root, exist_ok=True)
            os.makedirs(header_core_c_dst_root, exist_ok=True)
            os.makedirs(header_core_async_c_dst_root, exist_ok=True)

            shutil.copy2(
                f"{self.TENSORFLOW_LITE_ROOT}/builtin_ops.h",
                header_dst_root,
            )

            shutil.copy2(
                f"{self.TENSORFLOW_LITE_ROOT}/c/c_api.h",
                header_c_dst_root,
            )
            shutil.copy2(
                f"{self.TENSORFLOW_LITE_ROOT}/c/c_api_experimental.h",
                header_c_dst_root,
            )
            shutil.copy2(
                f"{self.TENSORFLOW_LITE_ROOT}/c/c_api_types.h",
                header_c_dst_root,
            )
            shutil.copy2(f"{self.TENSORFLOW_LITE_ROOT}/c/common.h", header_c_dst_root)

            for file in os.listdir(core_c_header_source):
                if file.endswith(self.HEADER_SUFFIX):
                    shutil.copy2(
                        f"{core_c_header_source}/{file}", header_core_c_dst_root
                    )

            for file in os.listdir(core_async_c_header_source):
                if file.endswith(self.HEADER_SUFFIX):
                    shutil.copy2(
                        f"{core_async_c_header_source}/{file}",
                        header_core_async_c_dst_root,
                    )
