import os
import asyncio
from asyncio.events import AbstractEventLoop
from typing import Any, Dict
import nmcli
import yaml

from provisioning_module import ProvisioningModule


class MachineConfig(ProvisioningModule):
    def __init__(self) -> None:
        self.prev_config_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "store/machine_config.yaml"
        )
        self.hostname = "Mirte-XXXXX"
        self.configuration = {}
        self.stopped = False

    def start(self, mount_point: str, loop: AbstractEventLoop) -> None:
        config_file = f"{mount_point}/machine_config.yaml"
        if not os.path.isfile(config_file):
            print("No machine_config configuration, stopping config provisioning")
            self.write_back_configuration({}, config_file)
            return

        with open(config_file, "r", encoding="utf-8") as file:
            self.configuration = yaml.safe_load(file)
        with open(self.prev_config_file, "r", encoding="utf-8") as file:
            prev_configuration = yaml.safe_load(
                file
            )  # this file should have all the configuration options
        self.configuration = {**prev_configuration, **self.configuration}
        if "hostname" in self.configuration:
            self.set_hostname(
                self.configuration["hostname"], prev_configuration["hostname"]
            )
        if "access_points" in self.configuration:
            self.access_points(self.configuration, loop)
        if "password" in self.configuration:
            self.set_password(
                self.configuration["password"], prev_configuration["password"]
            )  # todo: do only when not already done
        self.write_back_configuration(self.configuration, config_file)
        self.store_prev_config(self.configuration, self.prev_config_file)

    def access_points(
        self, configuration: Dict[str, Any], loop: AbstractEventLoop
    ) -> None:
        print(configuration)
        try:
            for ap in configuration["access_points"]:
                print(ap)
            loop.create_task(self.ap_loop(configuration))

        except Exception as e:
            print(e)

    def stop(self) -> None:
        self.stopped = True

    # Nmcli can only connect to a network that is in the air, so we need to
    # continuously check available networks and if not connected, try any
    # known connections
    async def ap_loop(self, configuration: Dict[str, Any]) -> None:
        while not self.stopped:
            await asyncio.sleep(10)
            await self.check_ap(configuration)

    async def check_ap(self, configuration: Dict[str, Any]) -> None:
        connections = nmcli.connection()
        wifi_conn = list(
            filter(
                lambda conn: conn.conn_type == "wifi" and conn.device != "--",
                connections,
            )
        )
        if len(wifi_conn) > 0:
            connection = wifi_conn[0]
            if connection.name != self.hostname:  # we have a connection to a wifi point
                print("existing wifi connection")
                return
        # No connection or own hotspot
        aps = list(map(lambda ap: ap.ssid, nmcli.device.wifi()))
        existing_known_aps = list(
            filter(
                lambda known_ap: known_ap["ssid"] in aps, configuration["access_points"]
            )
        )
        # keep ordering of known aps
        if len(existing_known_aps) > 0:
            ap = existing_known_aps[0]
            print(f"connecting to {ap}")
            nmcli.device.wifi_connect(ap["ssid"], ap["password"])

    def set_hostname(self, new_hostname: str, curr_set_hostname: str) -> None:
        if new_hostname == curr_set_hostname:
            return
        with open("/etc/hostname", "r", encoding="utf-8") as file:
            old_name = file.readlines()[0].strip()
            self.hostname = old_name
            if new_hostname == old_name:
                return
        print(f"Renaming from {old_name} to {new_hostname}")
        with open("/etc/hostname", "w", encoding="utf-8") as file:
            file.writelines(f"{new_hostname}\n")
            self.hostname = new_hostname

    def set_password(self, new_password: str, prev_set_password: str) -> None:
        if new_password == prev_set_password:
            # No need to update it and possibly the user edited it already by using
            # the passwd command
            return
        if (
            len(new_password) < 1
        ):  # when changing as the mirte user, there are some checks, when changing as root, no checks
            return
        print(f'Changing password to "{new_password}"')
        print(f'echo "echo "mirte:{new_password}" | chpasswd')
        o = os.system(f'echo "mirte:{new_password}" | chpasswd')
        print(o)

    def write_back_configuration(self, configuration: dict, config_file: str) -> None:
        # read back in the hostname file, if not set in this run, then the user
        # can know the hostname after a first boot
        with open("/etc/hostname", "r", encoding="utf-8") as file:
            current_name = file.readlines()[0].strip()
        # if XXXXX, then network setup did not set the hostname yet
        if current_name != "Mirte-XXXXXX":
            configuration["hostname"] = current_name
        config_text = yaml.dump(configuration)
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(config_text)

    def store_prev_config(
        self, configuration: Dict[str, Any], prev_config_file: str
    ) -> None:
        config_text = yaml.dump(configuration)
        with open(prev_config_file, "w", encoding="utf-8") as file:
            file.writelines(config_text)
