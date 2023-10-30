# Run scripts on the sd-card that have not yet ran
import os
import hashlib
import yaml
import subprocess
import signal
import time

processes = []


def start(mount_point, loop):
    loop.create_task(install_ros_packages(mount_point))


def stop():
    print("stop ROS packages")


async def install_ros_packages(mount_point):
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
        for package in new_packages:
            os.symlink(
                os.path.join(packages_folder, package),
                os.path.join(target_ws_folder, package),
            )
    except Exception as e:
        print(e)


def get_ws_folder():
    ret = subprocess.run(
        f'/bin/bash -c ". /home/mirte/.bashrc && roscd && pwd"',
        # f'/usr/bin/zsh -c ". /home/arendjan/.zshrc && roscd && pwd"',
        capture_output=True,
        shell=True,
    )
    print(ret.stdout.decode(), ret.stderr.decode())
    return os.path.abspath(os.path.join(ret.stdout.decode(), "../src"))
