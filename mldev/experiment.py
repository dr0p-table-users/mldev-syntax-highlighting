# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

"""
Experiments module
==================

This module contains basic tag types to define an experiment with MLDev.

- ``GenericPipeline`` is a sequence of steps (staged) with added services
- ``BasicStage`` is a simple step in a pipeline
- ``MonitoringService`` is a base class for services
- ``FilePath`` is a utility data type that defines a path with several files within

"""
import inspect

from mldev.experiment_tag import experiment_tag
from mldev.utils import *
from mldev import *

from mldev.yaml_loader import stage_context

from mldev.experiment_tag import experiment_tag
from mldev.python_context import PythonFunction


@experiment_tag()
class BasicStage(object):
    """
    A main class for non-versioned pipeline stages

    Defines a step in a pipeline that can be recalculated given ``inputs`` to
    product ``outputs``.

    The pipeline, the stage participated in, first calls ``stage.prepare(name)`` method.
    The stage has to initialize all its dependencies and return with no error
    if it is ready to be run. If stage cannot run, it should raise an exception
    to prevent the pipeline from proceeding.

    If a stage does not define the ``prepare`` method, it is skipped.

    After that the pipeline call the stage instance via ``__call__`` method,
    that is ``stage(name)``. This method should check if actual execution is needed
    or results are already fresh enough and then call ``stage.run()``.

    The ``stage.run()`` method does the actual execution.
    It runs the ``script`` by default using the default shell via ``utils.exec_command``.

    Any configuration for pipeline and stage execution comes from ``MLDevSettings()``.


    :param inputs: lists files and folders that this stage depends upon
    :param outputs: lists files and folders that this stage produces and that will be added to version control
    :param params: parameters for the commands being invoked
    :param env: additional environmental variables to pass to commands
    :param script: a list of command to invoke
    """

    def __init__(self, name="", params={}, env={}, inputs={}, outputs={}, script=[]):
        super().__init__()
        self.name = name
        self.params = params
        self.env = env
        self.inputs = inputs
        self.outputs = outputs
        self.script = script

    def __repr__(self):
        with stage_context(self):
            return str(self.__dict__)

    def __call__(self, name, *args, experiment={}, **kwargs):
        """
        Called by the pipeline. By default, expects ``name`` as the first parameter.
        Other parameters are ignored by ``BasicStage``.

        :param args: args[0] is the name of the stage
        :param kwargs: not used by ``BasicStage``
        :return:
        """
        with stage_context(self):
            stage_name = name if name else self.name
            logger.debug(f"{self.__class__.__name__}({stage_name}).__call__()")
            if stage_name:
                if not MLDevSettings().is_feature("FORCE_RUN"):
                    output_min, output_max, outputs_missing = self._get_modified_range(self.outputs)
                    input_min, input_max, inputs_missing = self._get_modified_range(self.inputs)

                    if not inputs_missing and not outputs_missing and output_min > input_max:
                        # assume nothing changed
                        logger.info(f"Unchanged ({stage_name})")
                        return

                self.run(stage_name)

                # update access and modification times
                set_path_times(self.outputs)

    def _get_modified_range(self, paths):

        min_ts = time.time()
        max_ts = 0

        missing = True
        for file_path in paths:
            if isinstance(file_path, FilePath):
                for file in file_path.get_files(start=os.path.curdir):
                    min_ts, max_ts, missing = get_path_times(file, min_ts, max_ts)

                if len(file_path.files) == 0:
                    min_ts, max_ts, missing = get_path_times(file_path.path, min_ts, max_ts)

            else:
                min_ts, max_ts, missing = get_path_times(file_path, min_ts, max_ts)

        return min_ts, max_ts, missing

    def prepare(self, stage_name):
        """
        Called by the pipeline. By default does nothing.

        :param stage_name: a name of the stage
        :return:
        """
        pass

    def run(self, stage_name):
        """
        Called by the pipeline. Enter the ``stage_context`` and executes the script.

        :param stage_name: a name of the stage
        :return:
        """
        with stage_context(self):
            # always show user program output
            capture = False # not (MLDevSettings().get_value("LOG_LEVEL") < LOG_INFO)

            script = prepare_experiment_command(' && '.join([str(s) for s in self.script]),
                                                    env=self.env)
            exec_command(script, capture=capture)


@experiment_tag()
class MonitoringService(object):
    """
    A common superclass for services accompanying the experiment

    Uses the following configuration parameters:
    - ``MLDevSettings().temp_dir`` for the directory for mldev temp files
    - ``MLDevSettings().tool_dir`` for the install directory of mldev

    """

    def __init__(self, name=None, params={}):
        super().__init__()
        self.name = name
        self.params = params
        self.error_file = MLDevSettings().temp_dir
        self.config_dir = MLDevSettings().tool_dir
        self.temp_dir = MLDevSettings().temp_dir
        self.logs_dir = os.path.join(self.temp_dir, 'logs')

        os.makedirs(self.error_file, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def __repr__(self):
        return "{}(name={}, params={})".format(
            self.__class__.__name__,
            self.name,
            self.params
        )

    def __call__(self, service_name):
        pass

    def prepare(self, service_name):
        pass


@experiment_tag()
class GenericPipeline(object):
    """
    This is a basic pipeline to run stages and services in a sequence

    Supports the following kinds of operation
     - sequence of runs - then use `runs` attribute in experiment.yml,
       expects **instances** of stages, for example using yaml anchors.
     - services and stages separately - first runs services, then stages,
       expects **attribute names** of top-level services and stages
       in the experiment spec in yaml. This does not requre use of yaml anchors.

    When using runs, it executes 'prepare' and then calls the items in the order specified

    The pipeline is a ``Callable`` and invoked as ``pipeline()``.
    The pipeline can be called in ``mode='prepare'`` then it iterates over

    :param runs: (optional) a list of stages or services in this pipeline, in the order to be run
    :param stages: (optional) alternative list of stages in the pipeline, runs after services
    :param services: (optional) a list of services, runs before stages
    """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.runs = kwargs.get('runs', [])
        self.stages = kwargs.get('stages', [])
        self.services = kwargs.get('services', [])
        pass

    def __call__(self, name, experiment={}, mode="run"):
        if mode == "prepare":
            self.run_services(experiment, mode)
            self.exec_stages(experiment, mode)
            self.exec_runs(experiment, mode)
        if mode == "run":
            self.run_services(experiment, mode)
            self.exec_stages(experiment, mode)
            self.exec_runs(experiment, mode)
        if mode is None:
            self.exec_runs(experiment, mode)
        pass

    def run_services(self, experiment_config, exec_type):
        for service_name in self.services:
            current_service = experiment_config.get(service_name)
            self.exec_item(current_service, experiment_config,
                           run_name=service_name, exec_type=exec_type)

    def exec_stages(self, experiment_config, exec_type):
        for stage_name in self.stages:
            current_stage = experiment_config.get(stage_name)
            if current_stage is None:
                raise Exception(f"Cannot find runnable item '{stage_name}' in the experiment")
            self.exec_item(current_stage, experiment_config,
                           run_name=stage_name, exec_type=exec_type)

    def exec_item(self, run, experiment_config, run_name=None, exec_type="run"):
        if not run_name and hasattr(run, "name"):
            run_name = run.name
        logger.info(f"{self.__class__.__name__} {exec_type}: {run_name}")
        if (exec_type is None or exec_type == "prepare") and hasattr(run, "prepare"):
            if callable(run.prepare):
                if "experiment" in inspect.signature(run.prepare).parameters:
                    run(run_name, experiment=experiment_config)
                run.prepare(run_name)
        if exec_type is None or exec_type == "run":
            if callable(run) and hasattr(run, "__call__") \
                    and "experiment" in inspect.signature(run.__call__).parameters:
                run(run_name, experiment=experiment_config)
            else:
                run(run_name)

    def exec_runs(self, experiment_config, exec_type):
        for run in self.runs:
            self.exec_item(run, experiment_config=experiment_config, exec_type=exec_type)

    @staticmethod
    def is_compatible(obj):
        if not callable(obj):
            logger.debug(f"{str(obj)} is not callable")
            return False
        if inspect.isfunction(obj):
            params = inspect.signature(obj).parameters
            if 'name' == next(iter(params)) \
                and 'mode' in params \
                and 'experiment' in params:
                logger.debug(f"Found pipeline compatible function {str(obj)}")
                return True
        if callable(obj) and hasattr(obj, "__call__"):
            params = inspect.signature(obj.__call__).parameters
            if 'name' == next(iter(params)) \
                and 'mode' in params \
                and 'experiment' in params:
                logger.debug(f"Found pipeline compatible __call__ method in {str(obj)}")
                return True

        return False


@experiment_tag(name="path")
class FilePath:
    """
    Implements a collection of files prefixed with a common path

    If cast to ``str``, produces a space separated list of absolute paths.
    > Note: this could cause problems if path of files contain unescaped spaces.

    When converted to json via ``to_json()`` produces a list of files from ``get_files()``

    :param path: (optional) a base path for the files and folders,
    defaults to experiment root if absent
    :param files: (optional) a list of files relative to the ``path``
    """

    def __init__(self, *args, **kwargs):
        self.path = kwargs.get("path", "")
        some_files = kwargs.get("files", [])
        self.files = []
        if some_files:
            if isinstance(some_files, str):
                self.files = [some_files]
            else:
                self.files = some_files

    def get_files(self, start=None):
        """
        Returns a list of paths to files in this ``FilePath``

        :param start: (optional) if present, paths are relative to ``start``, otherwise they are absolute
        :return:
        """
        if start is None:
            return [os.path.abspath(
                os.path.join(str(self.path), str(x))) for x in self.files if x is not None]
        else:
            return [os.path.relpath(
                os.path.join(str(self.path), str(x)), start) for x in self.files if x is not None]

    def get_path(self, start=None):
        """
        Returns a base path for this ``FilePath``

        :param start: (optional) if present, paths are relative to ``start``, otherwise they are absolute
        :return:
        """
        if start is None:
            return os.path.abspath(str(self.path))
        else:
            return os.path.relpath(str(self.path), start)

    def __str__(self):
        return self.get_path(start=os.path.curdir) \
            if len(self.files) == 0 \
            else " ".join([str(x) for x in self.get_files(start=os.path.curdir)])

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return str(self) == str(other)

    def to_json(self):
        return self.get_files()


__all__ = ['MonitoringService',
           'experiment_tag',
           'PythonFunction',
           'GenericPipeline',
           'BasicStage',
           'FilePath',
           'MLDevSettings']
