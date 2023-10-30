#!/usr/bin/python3
import time
import asyncio
import traceback

# Provisioning system for the Mirte sd cards.
# Only activate this service when you want to copy configurations from the second partition to the operating system

# assume mounting point is /mnt/mirte, otherwise change it here to somewhere to let the modules take out the required info
mount_point = "/mnt/mirte/"

import robot_config
import machine_config
import ssh

modules = [robot_config, machine_config, ssh]

event_loop = asyncio.get_event_loop()

for module in modules:
    try:
        module.start(mount_point, event_loop)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


async def main():
    count = 1000
    while True:
        count += -1
        await asyncio.sleep(1)


event_loop.run_until_complete(main())


for module in modules:
    try:
        module.stop()
    except Exception as e:
        print(e)

pending = asyncio.all_tasks(loop=event_loop)
event_loop.run_until_complete(asyncio.gather(*pending))
event_loop.close()
