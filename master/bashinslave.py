import uuid
import logging
import subprocess
import time


def execute_bash_script_in_slave_vm(slave_vm, script, verify_cert=True, interval=1, timeout=60, log_error=True):
    uid = uuid.uuid4()
    basedir = f"/tmp/{uid}"
    slave_vm.mkdir(basedir)
    script_path = f"{basedir}/script"
    output_path = f"{basedir}/output"
    slave_vm.put_file(script_path, script.encode(), verify_cert=verify_cert)
    pid = slave_vm.spawn_process_in_slave("/bin/bash", f"-c 'exec /bin/bash {script_path} > {output_path} 2>&1'")
    exitcode = slave_vm.wait_for_process_to_finish(pid=pid, interval=interval, timeout=timeout)
    output = slave_vm.get_file(output_path, verify_cert=verify_cert)
    slave_vm.rmdir_recursive(basedir)
    if exitcode != 0:
        if log_error:
            logging.error("Slave VM bash script exited with error: %s", output)
        raise subprocess.CalledProcessError(exitcode, "slave vm script", output)
    return output


def wait_for_slave_vm_to_wake_up(slave_vm, verify_cert=True, timeout=180):
    start = time.time()
    while True:
        time.sleep(1)
        try:
            execute_bash_script_in_slave_vm(
                slave_vm, "echo hi", verify_cert=verify_cert, timeout=10, log_error=False)
            return
        except Exception as e:
            if start + timeout > time.time():
                time.sleep(1)
            else:
                logging.exception("Timeout waiting for VM to wake up, last exception was:")
                raise Exception("Timeout waiting for VM to wake up")
