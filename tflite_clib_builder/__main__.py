""" MODULE DOC STRING """

import sys

import os

# import os.path
import shutil
import subprocess
import argparse

from tflite_clib_builder import builder_factory as factory

HOST_PLATFORM = "host"


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="build_c_lib",
        description=(
            "Builds tensorflow lite C shared library for specified architecture"
        ),
        # epilog="",
    )

    subparsers = parser.add_subparsers(required=True, help="Sub-Command help")

    configure_parser = subparsers.add_parser(
        "configure",
        help="Configure step for C library build",
    )

    configure_parser.add_argument(
        "--target_platform",
        "--os",
        choices=[*factory.BUILDER_PLATFORM_MAP.keys(), HOST_PLATFORM],
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

    # configure_parser.set_defaults(func=configure)

    build_parser = subparsers.add_parser(
        "build",
        help="Build step for C library build",
    )

    build_parser.add_argument(
        "--target_platform",
        "--os",
        choices=[*factory.BUILDER_PLATFORM_MAP.keys(), HOST_PLATFORM],
        type=str.lower,
        default=HOST_PLATFORM,
    )

    build_parser.add_argument("--dry_run", action="store_true")

    # build_parser.set_defaults(func=build)

    args = parser.parse_args()

    # args.func(args)
    builder = factory.get_builder(**vars(args))
    builder.configure()

    return 0


if __name__ == "__main__":
    sys.exit(main())
