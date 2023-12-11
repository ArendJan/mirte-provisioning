import os
from asyncio.events import AbstractEventLoop
from provisioning_module import ProvisioningModule

AUTH_KEYS_PATH = "/home/mirte/.ssh/authorized_keys"



class SshConfig(ProvisioningModule):
    def __init__(self) -> None:
        pass
    def start(self,mount_point: str, loop: AbstractEventLoop) -> None:
        config_file = f"{mount_point}/authorized_keys"
        if not os.path.isfile(config_file):
            print("No authorized keys configuration")
            return
        existing_keys = []
        with open(config_file, "r", encoding='utf-8') as file:
            new_keys = file.readlines()
        if os.path.isfile(AUTH_KEYS_PATH):
            with open(AUTH_KEYS_PATH, encoding='utf-8') as file:
                existing_keys = file.readlines()

        new_keys = list(filter(lambda key: key not in existing_keys, new_keys))
        print("adding:", new_keys)
        with open(AUTH_KEYS_PATH, "a", encoding='utf-8') as file:
            file.writelines(new_keys)


    def stop(self) -> None:
        print("stop ssh")
