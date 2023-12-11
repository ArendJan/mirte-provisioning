#!/usr/bin/python3

import time
import asyncio
import traceback
import signal
import functools
from asyncio.events import AbstractEventLoop
from typing import List

from provisioning_module import ProvisioningModule
from install_scripts import InstallScripts
from ssh import SshConfig
from machine_config import MachineConfig
from robot_config import RobotConfig
# Provisioning system for the Mirte sd cards.
# Only activate this service when you want to copy configurations from the
# second partition to the operating system

# assume mounting point is /mnt/mirte, otherwise change it here to
# somewhere to let the modules take out the required info
MOUNT_POINT = "/mnt/mirte/"
# mount_point = "/home/arendjan/mirte-provisioning/default_config/"

USED_MODULES = [ProvisioningModule(), InstallScripts(),SshConfig(), MachineConfig(), RobotConfig()]
stopped = False
event_loop = asyncio.get_event_loop()


def start_modules(mount_point:str, modules: List[ProvisioningModule], event_loop: AbstractEventLoop)-> None:
    for module in modules:
        try:
            module.start(mount_point, event_loop)
        except Exception as e:
            print(e)
            print(traceback.format_exc())


async def main_loop()-> None:
    while not stopped:
        await asyncio.sleep(0.5)
    print("stopped main")


def stop_all()-> None:
    global stopped
    stopped = True
    time.sleep(1)
    stop_modules(USED_MODULES)

    pending = asyncio.all_tasks(loop=event_loop)
    event_loop.run_until_complete(asyncio.gather(*pending))
    event_loop.close()


def stop_modules(modules:List[ProvisioningModule])-> None:
    for module in modules:
        try:
            module.stop()
        except Exception as e:
            print(e)


async def shutdown() -> None:
    global stopped
    stopped = True
    await asyncio.sleep(1)


def main():
    event_loop.add_signal_handler(
        signal.SIGINT, functools.partial(asyncio.ensure_future, shutdown())
    )
    event_loop.add_signal_handler(
        signal.SIGTERM, functools.partial(asyncio.ensure_future, shutdown())
    )

    start_modules(MOUNT_POINT, USED_MODULES, event_loop)
    event_loop.run_until_complete(main_loop())
    stop_all()


if __name__ == "__main__":
    main()
