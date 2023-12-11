import os
import shutil
import time
from asyncio.events import AbstractEventLoop
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


from provisioning_module import ProvisioningModule


class RobotConfig(ProvisioningModule):
    def __init__(self) -> None:
        self.observer = None
        self.tmx_config_path = "/usr/local/src/mirte/mirte-ros-packages/mirte_telemetrix/config/mirte_user_config.yaml"
        self.sd_config_path = "/mnt/mirte/robot_config.yaml"
        self.last_copy = time.time()

    def start(self, mount_point: str, loop: AbstractEventLoop) -> None:
        self.sd_config_path = f"{mount_point}/robot_config.yaml"
        if not os.path.isfile(self.tmx_config_path):
            print("No telemetrix configuration, stopping config provisioning")
            return
        if not os.path.isfile(self.sd_config_path):
            print("No configuration on extra partition, copying existing to it.")
            self.copy(self.tmx_config_path, self.sd_config_path)

        # Assuming the sd configuration is the 'latest', as it is either copied
        # from tmx/config or it is updated by the user when offline, so always
        # copy the sd config to the user_config
        self.copy(self.sd_config_path, self.tmx_config_path)
        observer = Observer()
        event_handler = self.MyEventHandler(self.copy_on_modify)
        observer.schedule(event_handler, self.tmx_config_path)
        observer.schedule(event_handler, self.sd_config_path)
        observer.start()

    def copy_on_modify(self, src_path: str) -> None:
        # otherwise it is triggering itself. 1s backoff time
        if time.time() - self.last_copy < 1:
            return
        self.last_copy = time.time()
        if src_path == self.tmx_config_path:
            self.copy(src_path, self.sd_config_path)
        else:  # TODO: restart telemetrix node
            self.copy(src_path, self.tmx_config_path)

    class MyEventHandler(FileSystemEventHandler):
        def __init__(self, copy_on_mod: Callable[[str], None]) -> None:
            super().__init__()
            self.copy_on_modify = copy_on_mod

        def catch_all_handler(self, event) -> None:
            if event.is_directory:
                return
            self.copy_on_modify(event.src_path)

        def on_moved(self, event):
            self.catch_all_handler(event)

        def on_created(self, event):
            self.catch_all_handler(event)

        def on_deleted(self, event):
            self.catch_all_handler(event)

        def on_modified(self, event):
            print(event)
            self.catch_all_handler(event)

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join()

    def copy(self, fr: str, to: str) -> None:
        shutil.copy2(fr, to)

    # sudo mount /dev/mmcblk0p2 /mnt/mirte  -o rw,uid=$(id -u),gid=$(id -g)

    #  status = os.stat(tmx_config_path)
    #     print(status)
    #     print(os.stat(f"{mount_point}robot_config.yaml"))
