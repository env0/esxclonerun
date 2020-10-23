import io
import tarfile
import json
import uuid
import textwrap
import bashinslave


class PythonPackage:
    def __init__(self, folder_path, entry_module, entry_function):
        self._entry_module = entry_module
        self._entry_function = entry_function
        self._compressed = self._compress_folder(folder_path)

    def run_in_slave(self, slave_vm, args=[], kwargs={}, verify_cert=True, interval=1, timeout=60):
        arguments_serialized = json.dumps(dict(args=args, kwargs=kwargs)).encode()
        uid = uuid.uuid4()
        basedir = f"/tmp/{uid}"
        slave_vm.mkdir(basedir)
        tarred_path = f"{basedir}/python_package.tar"
        entry_point = f"{basedir}/_entry_point.py"
        output_path = f"{basedir}/output_object.json"
        input_path = f"{basedir}/input_object.json"
        slave_vm.put_file(tarred_path, self._compressed, verify_cert=verify_cert)
        slave_vm.put_file(input_path, arguments_serialized, verify_cert=verify_cert)
        slave_vm.put_file(
            entry_point,
            textwrap.dedent("""
                import json
                with open('input_object.json') as reader:
                    arguments = json.load(reader)
                import %(entry_module)s
                output = %(entry_module)s.%(entry_function)s(*arguments['args'], **arguments['kwargs'])
                with open('output_object.json', 'w') as writer:
                    json.dump(output, writer)
            """ % dict(
                entry_module=self._entry_module,
                entry_function=self._entry_function,
            )),
            verify_cert=verify_cert)
        bashinslave.execute_bash_script_in_slave_vm(
            slave_vm=slave_vm,
            script=textwrap.dedent("""
                set +x
                set +e
                cd %(basedir)s
                tar -xf python_package.tar
                python3 _entry_point.py
            """ % dict(basedir=basedir)),
            verify_cert=verify_cert,
            interval=interval,
            timeout=timeout
        )
        output = slave_vm.get_file(output_path, verify_cert=verify_cert)
        slave_vm.rmdir_recursive(basedir)
        return json.loads(output.decode())

    @staticmethod
    def _compress_folder(folder_path):
        tar_fileobj = io.BytesIO()   
        with tarfile.open(fileobj=tar_fileobj, mode="w|") as tar:
            tar.add(folder_path, recursive=True, arcname='')
        tar_fileobj.seek(0) 
        return bytes(tar_fileobj.getbuffer())
