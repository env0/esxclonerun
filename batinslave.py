import uuid
import logging
import subprocess
import time


def execute_bat_script_in_slave_vm(slave_vm, guest_username, script, verify_cert=True, interval=1, timeout=60, log_error=True):
    uid = uuid.uuid4()
    temp_dir = f"C:\\Users\\{guest_username}\\AppData\\Local\\Temp"
    script_path = f"{temp_dir}\\script_{uid}.bat"
    output_path = f"{temp_dir}\\output_{uid}.txt"
    slave_vm.put_file(script_path, script.encode(), verify_cert=verify_cert)
    pid = slave_vm.spawn_process_in_slave("cmd.exe", f"/c \"{script_path} > {output_path}\"")
    exitcode = slave_vm.wait_for_process_to_finish(pid=pid, interval=interval, timeout=timeout)
    output = slave_vm.get_file(output_path, verify_cert=verify_cert)
    if exitcode != 0:
        if log_error:
            logging.error("Slave VM bat script exited with error: %s", output.decode())
        raise subprocess.CalledProcessError(exitcode, "slave vm script", output.decode())
    return output
