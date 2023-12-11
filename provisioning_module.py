from asyncio import AbstractEventLoop

class ProvisioningModule:
    def start(self, mount_point: str, loop: AbstractEventLoop) -> None:
        pass

    def stop(self) -> None:
        pass
