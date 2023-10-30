from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import shutil
import time

observer = None

tmx_config_path = "/usr/local/src/mirte/mirte-ros-packages/mirte_telemetrix/config/mirte_user_config.yaml"
sd_config_path = "/mnt/mirte/robot_config.yaml"


def start(mount_point, loop):
    global observer, sd_config_path
    sd_config_path = f"{mount_point}/robot_config.yaml"
    if not os.path.isfile(tmx_config_path):
        print("No telemetrix configuration, stopping config provisioning")
        return
    if not os.path.isfile(sd_config_path):
        print("No configuration on extra partition, copying existing to it.")
        copy(tmx_config_path, sd_config_path)

    # Assuming the sd configuration is the 'latest', as it is either copied from tmx/config or it is updated by the user when offline, so always copy the sd config to the user_config
    copy(sd_config_path, tmx_config_path)
    observer = Observer()
    event_handler = MyEventHandler()
    observer.schedule(event_handler, tmx_config_path)
    observer.schedule(event_handler, sd_config_path)
    observer.start()


last_copy = time.time()


def copy_on_modify(src_path):
    global last_copy
    # otherwise it is triggering itself. 1s backoff time
    if time.time() - last_copy < 1:
        return
    last_copy = time.time()
    if src_path == tmx_config_path:
        copy(src_path, sd_config_path)
    else:
        copy(src_path, tmx_config_path)


class MyEventHandler(FileSystemEventHandler):
    def catch_all_handler(self, event):
        if event.is_directory:
            return
        copy_on_modify(event.src_path)

    def on_moved(self, event):
        self.catch_all_handler(event)

    def on_created(self, event):
        self.catch_all_handler(event)

    def on_deleted(self, event):
        self.catch_all_handler(event)

    def on_modified(self, event):
        print(event)
        self.catch_all_handler(event)


def stop():
    observer.stop()
    observer.join()


def copy(fr, to):
    shutil.copy2(fr, to)


# sudo mount /dev/mmcblk0p2 /mnt/mirte  -o rw,uid=$(id -u),gid=$(id -g)

#  status = os.stat(tmx_config_path)
#     print(status)
#     print(os.stat(f"{mount_point}robot_config.yaml"))
