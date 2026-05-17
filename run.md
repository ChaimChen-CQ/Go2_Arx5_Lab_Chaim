# Go2Arm_Lab Run Commands

This file collects common commands for training, continuing training, and playing policies.
Replace paths in angle brackets with values from your machine.

## Setup

```bash
conda activate <ISAACLAB_CONDA_ENV>
cd <GO2ARM_LAB_ROOT>
python -m pip install -e source/Go2Arm_Lab
```

Example local values:

```bash
conda activate /home/chaim/miniconda3/envs/isaaclab
cd /home/chaim/Go2Arm_Lab
```

## Train From Scratch

```bash
python scripts/rsl_rl/train.py \
  --task Isaac-Go2Arm-Flat \
  --num_envs 2048 \
  --max_iterations 6000 \
  --headless
```

## Continue Training

Use this when you already have a run under `logs/rsl_rl/unitree_Go2arm_flat/`.

```bash
python scripts/rsl_rl/train.py \
  --task Isaac-Go2Arm-Flat \
  --num_envs 2048 \
  --resume \
  --load_run <RUN_DIR_NAME> \
  --checkpoint <CHECKPOINT_FILE> \
  --run_name <NEW_RUN_NAME> \
  --max_iterations 2000 \
  --headless
```

Example:

```bash
python scripts/rsl_rl/train.py \
  --task Isaac-Go2Arm-Flat \
  --num_envs 2048 \
  --resume \
  --load_run 2026-05-16_21-12-54_continue_2000 \
  --checkpoint model_2498.pt \
  --run_name continue_from_2498 \
  --max_iterations 2000 \
  --headless
```

## Short Validation Run

Use this after changing rewards, commands, actions, or robot configuration. It is faster than a full run and checks that training can start cleanly.

```bash
python scripts/rsl_rl/train.py \
  --task Isaac-Go2Arm-Flat \
  --num_envs 512 \
  --resume \
  --load_run <RUN_DIR_NAME> \
  --checkpoint <CHECKPOINT_FILE> \
  --run_name <TEST_RUN_NAME> \
  --max_iterations 300 \
  --headless
```

Example for the arm-extension and gait-tuning changes:

```bash
python scripts/rsl_rl/train.py \
  --task Isaac-Go2Arm-Flat \
  --num_envs 512 \
  --resume \
  --load_run 2026-05-16_21-12-54_continue_2000 \
  --checkpoint model_2498.pt \
  --run_name arm_extend_gait_test \
  --max_iterations 300 \
  --headless
```

## Play A Policy

```bash
python scripts/rsl_rl/play.py \
  --task Isaac-Go2Arm-Flat-Play \
  --num_envs 1 \
  --checkpoint <CHECKPOINT_PATH> \
  --real-time
```

Example:

```bash
python scripts/rsl_rl/play.py \
  --task Isaac-Go2Arm-Flat-Play \
  --num_envs 1 \
  --checkpoint /home/chaim/Go2Arm_Lab/logs/rsl_rl/unitree_Go2arm_flat/2026-05-17_14-49-56_arm_extend_gait_test/model_3497.pt \
  --real-time
```

## Debug Policy Tracking

```bash
python scripts/rsl_rl/debug_play_tracking.py \
  --task Isaac-Go2Arm-Flat-Play \
  --num_envs 1 \
  --checkpoint <CHECKPOINT_PATH> \
  --real-time
```

