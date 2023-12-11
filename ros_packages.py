# Run scripts on the sd-card that have not yet ran
import os
import hashlib
import yaml
import subprocess
import signal
import time
import asyncio
from urllib.request import urlopen
from asyncio.events import AbstractEventLoop
from typing import Any, Dict
from pathlib import Path


def start(mount_point: str, loop: AbstractEventLoop) -> None:
    loop.create_task(install_ros_packages(mount_point))


def stop() -> None:
    print("stop ROS packages")


async def install_ros_packages(mount_point: str) -> None:
    try:
        packages_folder = os.path.join(mount_point, "ros_packages")
        target_ws_folder = get_ws_folder()
        print(target_ws_folder)
        print(packages_folder)
        if not os.path.isdir(packages_folder):
            return  # no packages folder

        packages = [
            f
            for f in os.listdir(packages_folder)
            if os.path.isdir(os.path.join(packages_folder, f))
        ]
        existing_packages = [
            f
            for f in os.listdir(target_ws_folder)
            if os.path.isdir(os.path.join(target_ws_folder, f))
        ]
        print(packages, existing_packages)
        new_packages = [
            package for package in packages if package not in existing_packages
        ]
        print(new_packages)
        if len(new_packages) < 1:
            return
        for package in new_packages:
            try:
                os.symlink(
                    os.path.join(packages_folder, package),
                    os.path.join(target_ws_folder, package),
                )
            except Exception as e:
                print("symlink err:", e)
        # give the machine_config component time to connect to a nice network!
        await asyncio.sleep(20)
        rosdep_install()
    except Exception as e:
        print(e)


def get_ws_folder() -> str:
    ret = subprocess.run(
        f'/bin/bash -c ". /home/mirte/.bashrc && roscd && pwd"',
        # f'/usr/bin/zsh -c ". /home/arendjan/.zshrc && roscd && pwd"',
        capture_output=True,
        shell=True,
    )
    print(ret.stdout.decode(), ret.stderr.decode())
    return os.path.abspath(os.path.join(ret.stdout.decode(), "../src"))


def rosdep_install() -> None:
    if not internet_on():
        return
    ret = subprocess.run(
        "/bin/bash -c '. /home/mirte/.bashrc && roscd && cd ../src/ && p=$(pwd); rosdep install --from-paths $p --ignore-src -y -r -v'",
        # f'/usr/bin/zsh -c ". /home/arendjan/.zshrc && roscd && cd ../src/ && rosdep install {package} -r -s -i --rosdistro=$ROS_DISTRO"',
        capture_output=False,
        shell=True,
    )


def internet_on() -> bool:
    try:
        urlopen("https://mirte.org/", timeout=2)
        return True
    except BaseException:
        return False
