import logging
import time
import re
import requests
import pyVmomi


class SlaveVM:
    def __init__(self, esx_hostname, esx_content, expected_slave_vm_name, username, password):
        self._esx_hostname = esx_hostname
        self._esx_content = esx_content
        self._credentials = pyVmomi.vim.vm.guest.NamePasswordAuthentication(
            username=username,
            password=password)
        self._slave_vm = self._find_slave_vm(expected_slave_vm_name)
        self._process_manager = esx_content.guestOperationsManager.processManager
        self._file_manager = esx_content.guestOperationsManager.fileManager

    def verify_vm_tools_are_installed(self):
        status = self._slave_vm.guest.toolsStatus
        if status != "toolsOk":
            raise Exception(f"VM tools are not properly installed in slave vm: {status}")
        logging.info("Successfully verified VM tools installation in guest OS")

    def wait_for_vm_tools_to_be_installed(self, timeout=120, interval=1):
        start = time.time()
        while True:
            try:
                self.verify_vm_tools_are_installed()
                return
            except:
                if start + timeout > time.time():
                    time.sleep(interval)
                else:
                    raise

    def spawn_process_in_slave(self, executable_path, arguments):
        program_spec = pyVmomi.vim.vm.guest.ProcessManager.ProgramSpec(
            programPath=executable_path,
            arguments=arguments)
        pid = self._process_manager.StartProgramInGuest(self._slave_vm, self._credentials, program_spec)
        if pid <= 0:
            raise Exception(f"Unable to spawn executable {executable_path}: {pid}")
        logging.debug("Successfully spawned %s (pid %d)", executable_path, pid)
        return pid

    def wait_for_process_to_finish(self, pid, interval=0.5, timeout=60):
        started = time.time()
        logging.debug("Waiting on PID %d to exit", pid)
        exitcode = None
        while time.time() < started + timeout and exitcode is None:
            time.sleep(interval)
            exitcode = self._process_manager.ListProcessesInGuest(self._slave_vm, self._credentials, [pid]).pop().exitCode
        if exitcode is None:
            raise TimeoutError(f"Timeout waiting for pid {pid} to exit on slave VM")
        logging.debug("PID %d existed with exitcode %s", pid, exitcode)
        return int(exitcode)

    def mkdir(self, path):
        CREATE_PARENT_DIRECTORIES = True
        self._file_manager.MakeDirectoryInGuest(self._slave_vm, self._credentials, path, CREATE_PARENT_DIRECTORIES)
        logging.debug("Created directory %s in slave VM", path)

    def rmdir_recursive(self, path):
        self.spawn_process_in_slave("/bin/rm", "-fr " + path)
        logging.debug("Removing directory %s in slave VM", path)

    def put_file(self, filename, content, verify_cert=True):
        file_attribute = pyVmomi.vim.vm.guest.FileManager.FileAttributes()
        OVERWRITE = True
        url = self._file_manager.InitiateFileTransferToGuest(
            self._slave_vm,
            self._credentials,
            filename,
            file_attribute,
            len(content),
            OVERWRITE)
        response = requests.put(self._fix_url_for_public_hostname(url), data=content, verify=verify_cert)
        response.raise_for_status()
        logging.debug("Successfully uploaded %s to slave VM", filename)

    def get_file(self, filename, verify_cert=True):
        info = self._file_manager.InitiateFileTransferFromGuest(
            self._slave_vm,
            self._credentials,
            filename)
        response = requests.get(self._fix_url_for_public_hostname(info.url), verify=verify_cert)
        response.raise_for_status()
        logging.debug("Successfully downloaded %s from slave VM", filename)
        return response.content

    def _find_slave_vm(self, expected_slave_vm_name):
        children = self._esx_content.rootFolder.childEntity
        for child in children:
            if not hasattr(child, 'vmFolder'):
                continue
            vm_list = child.vmFolder.childEntity
            for vm in vm_list:
                if vm.name == expected_slave_vm_name:
                    logging.info("Slave VM found")
                    return vm
        raise Exception(f"VM with name {expected_slave_vm_name} was not found")

    def _fix_url_for_public_hostname(self, url):
        # When : host argument becomes https://*:443/guestFile?
        # Ref: https://github.com/vmware/pyvmomi/blob/master/docs/ \
        #            vim/vm/guest/FileManager.rst
        # Script fails in that case, saying URL has an invalid label.
        # By having hostname in place will take take care of this.
        return re.sub(r"^https://\*:", "https://"+str(self._esx_hostname)+":", url)
