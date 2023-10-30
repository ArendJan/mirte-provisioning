import yaml
import os
from deepdiff import DeepDiff
import nmcli
import asyncio

prev_config_file = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "store/machine_config.yaml"
)
print(prev_config_file)

hostname = "Mirte-XXXXX"


def start(mount_point, loop):
    config_file = f"{mount_point}/machine_config.yaml"
    if not os.path.isfile(config_file):
        print("No machine_config configuration, stopping config provisioning")
        write_back_configuration({}, config_file)
        return

    with open(config_file, "r") as file:
        configuration = yaml.safe_load(file)
    with open(prev_config_file, "r") as file:
        prev_configuration = yaml.safe_load(
            file
        )  # this file should have all the configuration options
    configuration = {**prev_configuration, **configuration}
    if "hostname" in configuration:
        set_hostname(configuration["hostname"], prev_configuration["hostname"])
    if "access_points" in configuration:
        access_points(configuration, loop)
    if "password" in configuration:
        set_password(
            configuration["password"], prev_configuration["password"]
        )  # todo: do only when not already done
    write_back_configuration(configuration, config_file)
    store_prev_config(configuration, prev_config_file)


def access_points(configuration, loop):
    print(configuration)
    try:
        for ap in configuration["access_points"]:
            print(ap)
        loop.create_task(ap_loop(configuration))

    except Exception as e:
        print(e)


stopped = False


def stop():
    global stopped
    stopped = True


# Nmcli can only connect to a network that is in the air, so we need to continuously check available networks and if not connected, try any known connections
async def ap_loop(configuration):
    while not stopped:
        await asyncio.sleep(10)
        await check_ap(configuration)


async def check_ap(configuration):
    connections = nmcli.connection()
    wifi_conn = list(
        filter(
            lambda conn: conn.conn_type == "wifi" and conn.device != "--", connections
        )
    )
    if len(wifi_conn) > 0:
        connection = wifi_conn[0]
        if connection.name != hostname:  # we have a connection to a wifi point
            print("existing wifi connection")
            return
    # No connection or own hotspot
    aps = nmcli.device.wifi()
    aps = list(map(lambda ap: ap.ssid, aps))
    # known_aps = list(map(lambda ap: ap.ssid, ))
    existing_known_aps = list(
        filter(lambda known_ap: known_ap["ssid"] in aps, configuration["access_points"])
    )
    # keep ordering of known aps
    if len(existing_known_aps) > 0:
        ap = existing_known_aps[0]
        print(f"connecting to {ap}")
        nmcli.device.wifi_connect(ap["ssid"], ap["password"])


def set_hostname(new_hostname, curr_set_hostname):
    global hostname
    if new_hostname == curr_set_hostname:
        return
    with open("/etc/hostname", "r") as file:
        old_name = file.readlines()[0].strip()
        hostname = old_name
        if new_hostname == old_name:
            return
    print(f"Renaming from {old_name} to {new_hostname}")
    with open("/etc/hostname", "w") as file:
        file.writelines(f"{new_hostname}\n")
        hostname = new_hostname


def set_password(new_password, prev_set_password):
    if new_password == prev_set_password:
        # No need to update it and possibly the user edited it already by using the passwd command
        return
    if (
        len(new_password) < 1
    ):  # when changing as the mirte user, there are some checks, when changing as root, no checks
        return
    print(f'Changing password to "{new_password}"')
    print(f'echo "{new_password}\n{new_password}" | sudo passwd mirte')
    o = os.system(f'echo "{new_password}\n{new_password}" | sudo passwd mirte')
    print(o)


def write_back_configuration(configuration, config_file):
    # read back in the hostname file, if not set in this run, then the user can know the hostname after a first boot
    with open("/etc/hostname", "r") as file:
        current_name = file.readlines()[0].strip()
    # if XXXXX, then network setup did not set the hostname yet
    if current_name != "Mirte-XXXXXX":
        configuration["hostname"] = current_name
    config_text = yaml.dump(configuration)
    with open(config_file, "w") as file:
        file.writelines(config_text)


def store_prev_config(configuration, prev_config_file):
    config_text = yaml.dump(configuration)
    with open(prev_config_file, "w") as file:
        file.writelines(config_text)
