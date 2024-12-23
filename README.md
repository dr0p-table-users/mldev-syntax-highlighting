# Repository structure
Repository contains two directoies:

1) demo. Is a monaco-editor with YAML syntax highlighting. Added MLDev tags for correct highlighting. Also, YAML schema is currently in progress...
2) mldev. Content of https://gitlab.com/mlrep/mldev/-/tree/develop/src/mldev?ref_type=heads with added script get_all_tags.py to find all yaml tags and put their names into Tags.txt (is used by demo)

# Demo
Run demo editor by executing the following commands:
```
cd demo
npm install
npm start
```

# Sample data
Taken from https://gitlab.com/mlrep/template-default/-/blob/master/experiment.yml
```
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://gitlab.com/mlrep/mldev/-/blob/master/NOTICE.md

prepare: &prepare_stage !BasicStage
  name: prepare
  params:
    size: 1
  inputs:
    - !path { path: "./src" }
  outputs:
    - !path { path: "./data" }
  script:
    - "python3 src/prepare.py"


train: &train_stage !BasicStage
  name: train
  params:
    num_iters: 10
  inputs:
    - !path
      path: "./data"
      files:
        - "X_train.pickle"
        - "X_dev.pickle"
        - "X_test.pickle"
        - "y_train.pickle"
        - "y_dev.pickle"
        - "y_test.pickle"
  outputs: &model_data
    - !path
      path: "models/default"
      files:
        - "model.pickle"
  script:
    - "python3 src/train.py --n ${self.params.num_iters}"

present_model: &present_model !BasicStage
  name: present_model
  inputs: *model_data
  outputs:
    - !path
      path: "results/default"
  env:
    MLDEV_MODEL_PATH: ${path(self.inputs[0].path)}
    RESULTS_PATH: ${self.outputs[0].path}
  script:
    - |
      python3 src/predict.py
      printf "=============================\n"
      printf "Test report:\n\n"
      cat ${path(self.outputs[0].path)}/test_report.json
      printf "\n\n=============================\n"

pipeline: !GenericPipeline
  runs:
    - *prepare_stage # prepare
    - *train_stage
    - *present_model # finals

```