import os
from asyncio.events import AbstractEventLoop

auth_keys_path = "/home/mirte/.ssh/authorized_keys"


def start(mount_point: str, loop: AbstractEventLoop) -> None:
    config_file = f"{mount_point}/authorized_keys"
    if not os.path.isfile(config_file):
        print("No authorized keys configuration")
        return
    existing_keys = []
    with open(config_file, "r") as file:
        new_keys = file.readlines()
    if os.path.isfile(auth_keys_path):
        with open(auth_keys_path) as file:
            existing_keys = file.readlines()

    new_keys = list(filter(lambda key: key not in existing_keys, new_keys))
    print("adding:", new_keys)
    with open(auth_keys_path, "a") as file:
        file.writelines(new_keys)


def stop() -> None:
    print("stop ssh")
