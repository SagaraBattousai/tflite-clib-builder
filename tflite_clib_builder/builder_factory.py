""" Factory module for Builders """
import sys

# from typing import Callable, Any

from tflite_clib_builder.builders.abstract_builder import AbstractBuilder
from tflite_clib_builder.builders.android_builder import AndroidBuilder
from tflite_clib_builder.builders.linux_builder import LinuxBuilder
from tflite_clib_builder.builders.windows_builder import WindowsBuilder

# Probably a cooler way to do this (without duplication)
BUILDER_PLATFORM_MAP: dict[str, type[AbstractBuilder]] = {
    AndroidBuilder.platform(): AndroidBuilder,
    LinuxBuilder.platform(): LinuxBuilder,
    WindowsBuilder.platform(): WindowsBuilder,
}


# May need to make more complex later (may also do stuff for cmake_args)
def get_builder(target_platform: str, **kwargs) -> AbstractBuilder:
    if target_platform in BUILDER_PLATFORM_MAP:
        return BUILDER_PLATFORM_MAP[target_platform](**kwargs)

    # target_platform == host (although it could be anything)
    if sys.platform.startswith("linux"):
        ##Not great for android but unlikly to be host
        return LinuxBuilder(**kwargs)
    if sys.platform.startswith("win32"):
        return WindowsBuilder(**kwargs)

    print(
        "Host platform is not directly supported, treating platform as Linux",
        file=sys.stderr,
    )
    return LinuxBuilder(**kwargs)
