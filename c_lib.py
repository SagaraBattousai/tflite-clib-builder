""" MODULE DOC STRING """

import sys

import os

# import os.path
import shutil
import subprocess
import argparse

TENSORFLOW_LITE_C_CMAKE_PATH = "../tensorflow_src/tensorflow/lite/c"

ANDROID_PLATFORM = "android"
WINDOWS_PLATFORM = "win"  # 32"
UNIX_PLATFORM = "unix"
HOST_PLATFORM = "host"

# HOST_PLATFORM must be last in the list!
PLATFORM_TYPES = [ANDROID_PLATFORM, WINDOWS_PLATFORM, UNIX_PLATFORM, HOST_PLATFORM]

ABSL_PROPOGATE_FLAG = "-DABSL_PROPAGATE_CXX_STD=ON"
BUILD_TYPE_FLAG = "-DCMAKE_BUILD_TYPE="

BUILD_OUTPUT_DIR_FILENAME = "c_lib_output_dir.txt"

LIB_BASE_NAME = "tensorflowlite_c"

UNIX_SHARED_LIB_EXT = ".so"
WIN_SHARED_LIB_EXT = ".dll"
WIN_LINK_LIB_EXT = ".lib"  # Could also be .dll.a

HEADER_INCLUDE_BASE_PATH = "include/tensorflow/lite"


HEADER_SOURCE_ROOT = "../tensorflow_src/tensorflow/lite"


# May need to make more complex later (may also do stuff for cmake_args)
def get_platform_for_host() -> str:
    if sys.platform.startswith("linux"):
        ##Not great for android but unlikly to be host
        return UNIX_PLATFORM
    if sys.platform.startswith("win32"):
        return WINDOWS_PLATFORM
    else:
        raise RuntimeError(
            "Host platform is not supported please choose an os from ",
            f"the following: {PLATFORM_TYPES[:-1]}",
        )


def get_cmake_args_for_os(ostype: str) -> tuple[list[str], str]:
    if ostype == HOST_PLATFORM:
        ostype = get_platform_for_host()

    os_args_map: dict[str, list[str]] = {
        ANDROID_PLATFORM: [],
        WINDOWS_PLATFORM: [
            "-DTFLITE_ENABLE_MMAP=OFF",
            "-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON",
        ],
        UNIX_PLATFORM: [],
    }

    return os_args_map[ostype], ostype


def configure(args):
    cmake_args, ostype = get_cmake_args_for_os(args.os)

    cmake_args.append(BUILD_TYPE_FLAG + args.build_type)

    cmake_args.append(ABSL_PROPOGATE_FLAG)

    # Separate for os's as they usually differ on the generator used
    # (will this cause issues with build types?) no point having individual build dirs
    # since that would be a huge waste
    build_root = ostype
    # Below is not used in this step but will be written to build dir to tell
    # it where do the build (also a good idea since we could reconfigure)
    output_dir = f"{build_root}/{args.build_type}"

    if args.os == ANDROID_PLATFORM:
        if not args.generator:
            args.generator = "Ninja"

        cmake_args.append("-DANDROID_STL=" + args.android_stl)

        cmake_args.append("-DANDROID_ABI=" + args.android_abi)

        # ABI comes before platform on path as we dont (for now) require platform.
        output_dir += f"/{args.android_abi}"

        if args.android_platform:
            cmake_args.append("-DANDROID_PLATFORM=" + args.android_platform)
            output_dir += f"/{args.android_platform}"

        if not args.android_sdk_path:
            raise RuntimeError(
                "When configuring for android, android_sdk_path must be set."
            )
        if not args.ndk_version:
            raise RuntimeError("When configuring for android, ndk_version must be set.")

        ndk_version_path = f"{args.android_sdk_path}/ndk/{args.ndk_version}"
        cmake_args.append("-DANDROID_NDK=" + ndk_version_path)
        cmake_args.append(
            f"-DCMAKE_TOOLCHAIN_FILE={ndk_version_path}/build/cmake/"
            "android.toolchain.cmake"
        )

    if args.generator:
        cmake_args.append(f"-G {args.generator}")

    build_dir = f"{build_root}/build"

    cmake_args.append(f"-B {build_dir}")

    cmake_args.append(f"-S {TENSORFLOW_LITE_C_CMAKE_PATH}")

    if args.dry_run:
        print("cmake", *cmake_args, sep="\n\t")
        print(f"mkdir {output_dir}")
        print(f"mkdir {build_dir}")
        print(f"echo {output_dir} >> {build_dir}/{BUILD_OUTPUT_DIR_FILENAME}")
    else:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(build_dir, exist_ok=True)
        with open(
            f"{build_dir}/{BUILD_OUTPUT_DIR_FILENAME}", "w", encoding="utf-8"
        ) as f:
            f.write(output_dir)
        subprocess.run(["cmake", *cmake_args], check=False)


def build(args):
    if args.os == HOST_PLATFORM:
        args.os = get_platform_for_host()

    build_dir = f"{args.os}/build"
    lib_dir = build_dir

    if args.os == WINDOWS_PLATFORM:
        lib_dir += "/Debug"

    lib_out = ""
    # TODO: Handle error file not exists etc
    with open(f"{build_dir}/{BUILD_OUTPUT_DIR_FILENAME}", "r", encoding="utf-8") as f:
        # Safe enough as should be small unless someone maliciously adds to it.
        lib_out = f.read()

    if args.dry_run:
        print("cmake", "--build", build_dir)
        if args.os == WINDOWS_PLATFORM:
            print(f"cp {lib_dir}/{LIB_BASE_NAME}{WIN_SHARED_LIB_EXT} -> {lib_out}")
            print(f"cp {lib_dir}/{LIB_BASE_NAME}{WIN_LINK_LIB_EXT} -> {lib_out}")
            # May need to check .dll.a if .lib is not found.
        else:
            print(f"cp {lib_dir}/{LIB_BASE_NAME}{UNIX_SHARED_LIB_EXT} -> {lib_out}")
    else:
        subprocess.run(["cmake", "--build", build_dir], check=True)

        if args.os == WINDOWS_PLATFORM:
            shutil.copy2(f"{lib_dir}/{LIB_BASE_NAME}{WIN_SHARED_LIB_EXT}", lib_out)
            shutil.copy2(f"{lib_dir}/{LIB_BASE_NAME}{WIN_LINK_LIB_EXT}", lib_out)
            # May need to check .dll.a if .lib is not found.
        else:
            shutil.copy2(f"{lib_dir}/{LIB_BASE_NAME}{UNIX_SHARED_LIB_EXT}", lib_out)

    header_dst_root = f"{lib_out}/{HEADER_INCLUDE_BASE_PATH}"
    header_c_dst_root = f"{lib_out}/{HEADER_INCLUDE_BASE_PATH}/c"
    header_core_c_dst_root = f"{lib_out}/{HEADER_INCLUDE_BASE_PATH}/core/c"
    header_core_async_c_dst_root = f"{lib_out}/{HEADER_INCLUDE_BASE_PATH}/core/async/c"

    os.makedirs(header_c_dst_root, exist_ok=True)
    os.makedirs(header_core_c_dst_root, exist_ok=True)
    os.makedirs(header_core_async_c_dst_root, exist_ok=True)

    shutil.copy2(f"{HEADER_SOURCE_ROOT}/builtin_ops.h", header_dst_root)

    shutil.copy2(f"{HEADER_SOURCE_ROOT}/c/c_api.h", header_c_dst_root)
    shutil.copy2(f"{HEADER_SOURCE_ROOT}/c/c_api_experimental.h", header_c_dst_root)
    shutil.copy2(f"{HEADER_SOURCE_ROOT}/c/c_api_types.h", header_c_dst_root)
    shutil.copy2(f"{HEADER_SOURCE_ROOT}/c/common.h", header_c_dst_root)

    core_c_headers = filter(
        lambda s: s.endswith(".h"),
        os.listdir(f"{HEADER_SOURCE_ROOT}/core/c"),
    )

    for header in core_c_headers:
        shutil.copy2(f"{HEADER_SOURCE_ROOT}/core/c/{header}", header_core_c_dst_root)

    core_async_c_headers = filter(
        lambda s: s.endswith(".h"),
        os.listdir(f"{HEADER_SOURCE_ROOT}/core/async/c"),
    )

    for header in core_async_c_headers:
        shutil.copy2(
            f"{HEADER_SOURCE_ROOT}/core/async/c/{header}", header_core_async_c_dst_root
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="build_c_lib",
        description="Builds tensorflow lite C shared library "
        "for specified architecture",
        # epilog="",
    )

    subparsers = parser.add_subparsers(required=True, help="Sub-Command help")

    configure_parser = subparsers.add_parser(
        "configure",
        help="Configure step for C library build",
    )

    configure_parser.add_argument(
        "--os",
        choices=PLATFORM_TYPES,
        type=str.lower,
        default=HOST_PLATFORM,
    )

    configure_parser.add_argument(
        "--build_type",
        choices=["Debug", "Release"],
        type=str.capitalize,
        default="Release",
    )

    # # Find way to add this to parent parser as is used by both
    # configure_parser.add_argument("-b", "--build_dir", default=os.getcwd())

    # Find way to add this to parent parser as is used by both
    configure_parser.add_argument("-g", "-G", "--generator")

    configure_parser.add_argument(
        "--android_stl",
        choices=["c++_shared", "c++_static", "none", "system"],
        type=str.lower,
        default="c++_shared",
    )

    # Could make int and prepend android-
    configure_parser.add_argument(
        "--android_platform",
        type=str.lower,
    )

    configure_parser.add_argument(
        "--android_abi",
        choices=["arm64-v8a", "armeabi-v7a", "x86_64", "x86"],
        type=str.lower,
        default="arm64-v8a",
    )

    configure_parser.add_argument(
        "--android_sdk_path",
        type=str.lower,
    )

    configure_parser.add_argument(
        "--ndk_version",
        type=str.lower,
    )

    configure_parser.add_argument("--dry_run", action="store_true")

    configure_parser.set_defaults(func=configure)

    build_parser = subparsers.add_parser(
        "build",
        help="Build step for C library build",
    )

    build_parser.add_argument(
        "--os",
        choices=PLATFORM_TYPES,
        type=str.lower,
        default=HOST_PLATFORM,
    )

    build_parser.add_argument("--dry_run", action="store_true")

    build_parser.set_defaults(func=build)

    args = parser.parse_args()

    args.func(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
