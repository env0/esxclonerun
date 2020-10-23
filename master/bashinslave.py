import uuid
import logging
import subprocess


def execute_bash_script_in_slave_vm(slave_vm, script, verify_cert=True, interval=1, timeout=60):
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
        logging.error("Slave VM bash script exited with error: %s", output)
        raise subprocess.CalledProcessError(exitcode, "slave vm script", output)
    return output
