# Run scripts on the sd-card that have not yet ran
from asyncio.events import AbstractEventLoop
import os
import subprocess
import signal
import time
from typing import Any, List
import yaml

from provisioning_module import ProvisioningModule


class InstallScripts(ProvisioningModule):
    def __init__(self)->None:
        self.processes:List[subprocess.Popen] = []

    def start(self, mount_point: str, loop: AbstractEventLoop) -> None:
        loop.create_task(self.install_scripts(mount_point))

    def stop(self) -> None:
        # stop all started scripts, giving them 10 seconds between sigint and
        # killing them.
        for proc in self.processes:
            try:
                if proc.poll() is None:
                    proc.send_signal(signal.SIGINT)
                    start_time = time.time()
                    while proc.poll() is None and time.time() - start_time < 10:
                        time.sleep(0.2)
                    if proc.poll() is None:
                        proc.terminate()
                print("stopped ", proc.args[1])
            except Exception as e:
                print(e)
        print("stop install_scripts")

    async def install_scripts(self, mount_point: str) -> None:
        # run all scripts if not yet ran(checked by sha256sum check), but if ends
        # with _always, then start it always
        try:
            scripts_folder = os.path.join(mount_point, "scripts")
            print(scripts_folder)
            if not os.path.isdir(scripts_folder):
                return  # no scripts folder
            ran_scripts_file = os.path.join(
                mount_point, "scripts/ran_scripts.yaml")
            print(ran_scripts_file)
            if not os.path.isfile(ran_scripts_file):
                with open(ran_scripts_file, "w", encoding='utf-8') as file:
                    file.writelines("")
            scripts = [
                os.path.join(scripts_folder, f)
                for f in os.listdir(scripts_folder)
                if os.path.isfile(os.path.join(scripts_folder, f)) and f.endswith(".sh")
            ]
            always_scripts = [
                script for script in scripts if "always" in script]
            once_scripts = [
                script for script in scripts if "always" not in script]
            self.start_always_scripts(always_scripts)
            script_hashes = self.get_script_hashes(ran_scripts_file)

            self.start_once_scripts(once_scripts, script_hashes)
            self.write_script_hashes(ran_scripts_file, script_hashes)
        except Exception as e:
            print(e)

    def write_script_hashes(
        self, ran_scripts_file: str, script_hashes: List[Any]
    ) -> None:
        with open(ran_scripts_file, "w", encoding='utf-8') as file:
            file.writelines(yaml.dump(script_hashes))

    def start_once_scripts(
            self,
            once_scripts: List[str],
            script_hashes: Any) -> None:
        for script in once_scripts:
            # check hash change
            self.start_once_script(script, script_hashes)

    def start_once_script(self, script: str, script_hashes: Any) -> None:
        index = -1
        found_files = [i for i, e in enumerate(
            script_hashes) if e["file"] == script]
        if len(found_files) == 1:
            index = found_files[0]
        if index != -1:
            ret = subprocess.run(
                f"echo \"{script_hashes[index]['sha256sum']}\" | sha256sum -c --status",
                capture_output=True,
                shell=True, check=False
            )
            if ret.returncode == 0:
                # no change, return
                return
        ret = subprocess.run(  # there is a file change, so we should get a new hash.
            f"sha256sum {script}",
            capture_output=True,
            shell=True, check=False
        )
        checksum = ret.stdout.decode().strip()
        if index == -1:
            script_hashes.append({"file": script, "sha256sum": checksum})
        else:
            script_hashes[index]["sha256sum"] = checksum  # update when changed
        self.start_script(script)

    def get_script_hashes(self, ran_scripts_file: str) -> Any:
        with open(ran_scripts_file, "r", encoding='utf-8') as file:
            script_hashes = yaml.safe_load(file)
            if script_hashes is None:
                script_hashes = []
        return script_hashes

    def start_always_scripts(self, always_scripts: List[str]) -> None:
        for script in always_scripts:
            self.start_script(script)

    def start_script(self, script_name: str) -> None:
        # FAT filesystems don't have the executable flag, so directly running it won't work, so just start them with bash
        # also start them in the background
         # pylint: disable=consider-using-with
        proc = subprocess.Popen(["/bin/bash", script_name])
        self.processes.append(proc)
