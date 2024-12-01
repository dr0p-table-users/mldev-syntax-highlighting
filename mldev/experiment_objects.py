# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

import yaml
import sh

from mldev.experiment import *
from mldev.utils import *
from mldev import *


@experiment_tag()
class NgrokService(MonitoringService):
    """
    This service helps access other services running behind NAT

    It employs `ngrok` web service to set up a secure tunnel to the host it runs
    on from the Internet

    Note: you need to provide a valid `NGROK_TOKEN` in mldev config or
    as an environmental variable

    You can get URLs for the running services using `mldev urls` command

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_dir = os.path.join(self.temp_dir, "ngrok")
        os.makedirs(self.temp_dir, exist_ok=True)

    def __call__(self, *args, **kwargs):
        ngrok_config = {"tunnels": {}}
        for port in self.params.get("ports", [6006]):
            ngrok_config["tunnels"][f"tunnel{port}"] = \
                {"proto": "http", "addr": str(port), "bind_tls": "false"}
        with open(f"{self.temp_dir}/ngrok.yml", "w") as ngrok_config_file:
            yaml.dump(ngrok_config, ngrok_config_file)

        sh.Command(f"{self.temp_dir}/ngrok")\
                            ("start",
                              f"-config={self.temp_dir}/ngrok.yml", "--all",
                              _out=f"{self.temp_dir}/ngrok.log",
                              _err=f"{self.temp_dir}/ngrok.err",
                              _bg=True)
        logger.info("view tensorboard stats: ")
        exec_tool_command("ngrok_urls.sh")

    def prepare(self, service_name):
        if not os.path.isfile(f"{self.temp_dir}/ngrok"):
            exec_tool_command(f"install_ngrok.sh {self.temp_dir}")
        try:
            check_kill_process("ngrok")
        except sh.SignalException:
            pass

        sh.Command(f"{self.temp_dir}/ngrok")("authtoken", str(self.params.get("token")))


@experiment_tag()
class ForEach(object):

    def __init__(self, collection=[], commands=[]):
        super().__init__()
        self.collection = collection
        self.commands = commands

    def __repr__(self):
        return "{}(collection={}, commands={})".format(
            self.__class__.__name__,
            self.collection,
            self.commands
        )

    def __call__(self, *args, **kwargs):
        for item in self.collection:
            if self.commands:
                for command in self.commands:
                    exec_command(command)
            self.collection.get(item)(item)


@experiment_tag()
class If(object):

    def __init__(self, statement=None, true_case={}, false_case={}):
        super().__init__()
        self.statement = statement
        self.true_case = true_case
        self.false_case = false_case

    def __repr__(self):
        return "{}(statement={}, true_case={}, false_case={})".format(
            self.__class__.__name__,
            self.statement,
            self.true_case,
            self.false_case
        )

    def __call__(self, *args, **kwargs):
        if self.statement:
            for operation in self.true_case:
                # print("TRUE" + operation)
                operation()
        else:
            for operation in self.false_case:
                # print("FALSE" + operation)
                operation()



