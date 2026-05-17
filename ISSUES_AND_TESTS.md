# Recent Issues, Changes, And Test Notes

本文档记录最近 Go2Arm flat 任务的主要问题、已经做过的修改、测试现象和下一步调参方向。

## 当前问题

### 1. 机器人已经可以行走，但步态不够协调

当前策略可以让 Go2Arm 在 flat 场景中向前移动，但视觉效果仍然不理想：

- 腿部动作不够自然，存在拖脚或步幅不稳定的现象。
- 身体姿态和腿部摆动协调性一般。
- 速度跟踪可以工作，但动作观感还没有形成稳定、清晰的四足步态。

### 2. 机械臂大臂关节仍然不主动展开

测试中观察到机械臂末端 marker 在前方，但机械臂大臂关节没有明显伸展：

- 大臂更倾向保持收缩或小幅运动。
- 末端位置跟踪 reward 还不足以驱动机械臂主动伸向目标。
- 机械臂动作可能受到动作平滑惩罚、姿态惩罚、动作尺度或训练不足的共同影响。

## 已经完成的修改

### 训练稳定性修改

文件：

- `source/Go2Arm_Lab/Go2Arm_Lab/assets/go2_arx5_articulation_cfg.py`
- `source/Go2Arm_Lab/Go2Arm_Lab/tasks/manager_based/go2arm_lab/config/flat_env_cfg.py`
- `source/Go2Arm_Lab/Go2Arm_Lab/tasks/manager_based/go2arm_lab/go2arm_lab_env_cfg.py`
- `source/Go2Arm_Lab/Go2Arm_Lab/tasks/manager_based/go2arm_lab/mdp/rewards.py`

主要调整：

- 将腿部 actuator 从 `DelayedPDActuatorCfg` 改为 `DCMotorCfg`。
- 关闭 self-collision，增加 velocity solver iteration。
- 收窄 reset 初始扰动，降低初始随机性。
- 增加 `root_height_below_minimum` 终止条件，避免机器人过低姿态继续训练。
- 降低部分动作惩罚，增强前向速度跟踪。

效果：

- 机器人已经可以走起来。
- 基础 locomotion 明显比之前稳定。
- 但步态观感仍需要继续优化。

### 机械臂伸展相关修改

文件：

- `source/Go2Arm_Lab/Go2Arm_Lab/tasks/manager_based/go2arm_lab/config/flat_env_cfg.py`
- `source/Go2Arm_Lab/Go2Arm_Lab/tasks/manager_based/go2arm_lab/go2arm_lab_env_cfg.py`
- `source/Go2Arm_Lab/Go2Arm_Lab/tasks/manager_based/go2arm_lab/mdp/rewards.py`

主要调整：

- 将 ee pose command 的 `pos_x` 范围整体前移：
  - init: `(0.55, 0.62)`
  - final: `(0.55, 0.72)`
  - play: `(0.58, 0.72)`
- 加快机械臂 command curriculum：
  - `curriculum_coeff = 2500`
- 加强末端位置跟踪：
  - `end_effector_position_tracking.weight = 5.0`
  - `std = 0.15`
- 新增前向伸展 reward：
  - `position_command_x_error_exp`
  - `end_effector_forward_tracking.weight = 2.0`
- 放松机械臂动作惩罚：
  - `end_effector_action_rate.weight = -0.003`
  - `end_effector_action_smoothness.weight = -0.01`
- 增大部分机械臂动作尺度：
  - `joint2 = 0.65`
  - `joint3 = 0.65`
  - `joint4 = 0.55`
- 降低末端姿态惩罚：
  - `end_effector_orientation_tracking.weight = -0.5`

当前测试结论：

- 这些修改已经写入训练配置，但旧 checkpoint 不会自动体现新 reward。
- 需要从旧 checkpoint 继续训练一段时间，才能判断机械臂是否学会主动展开。
- 截至目前，问题仍未完全解决：大臂仍有不展开现象。

### 步态观感相关修改

文件：

- `source/Go2Arm_Lab/Go2Arm_Lab/tasks/manager_based/go2arm_lab/config/flat_env_cfg.py`

主要调整：

- 增强前后脚 air-time reward：
  - `F_feet_air_time.weight = 0.55`
  - `R_feet_air_time.weight = 0.55`
  - threshold 从 `0.2` 增加到 `0.25`
- 恢复脚高度相关 penalty：
  - `feet_height.weight = -0.35`
  - `feet_height.target_height = 0.08`
  - `feet_height_body.weight = -0.8`
  - `feet_height_body.target_height = -0.23`
- 稍微增强腿部动作平滑和关节偏离惩罚：
  - `hip_deviation.weight = -0.08`
  - `joint_deviation.weight = -0.004`
  - `action_smoothness.weight = -0.008`

当前测试结论：

- 修改目标是减少拖脚，让步态有更明显的摆腿和落脚。
- 这些 reward 也需要继续训练后才能看出稳定效果。
- 目前仍存在移动不协调问题。

## 推荐测试命令

先进行短训练验证，确认代码和 reward 修改不会导致训练崩溃：

```bash
conda activate /home/chaim/miniconda3/envs/isaaclab
cd /home/chaim/Go2Arm_Lab

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

如果 300 iteration 没有报错，再继续更长训练：

```bash
python scripts/rsl_rl/train.py \
  --task Isaac-Go2Arm-Flat \
  --num_envs 2048 \
  --resume \
  --load_run <LATEST_TEST_RUN> \
  --checkpoint <LATEST_MODEL_FILE> \
  --run_name arm_extend_gait_continue \
  --max_iterations 2000 \
  --headless
```

播放新模型：

```bash
python scripts/rsl_rl/play.py \
  --task Isaac-Go2Arm-Flat-Play \
  --num_envs 1 \
  --checkpoint <NEW_CHECKPOINT_PATH> \
  --real-time
```

## 观察指标

播放时重点看：

- 机械臂大臂是否主动向前展开。
- 末端是否靠近蓝绿 marker 的目标位置。
- 机器人是否仍能保持稳定向前走。
- 是否出现为了伸机械臂而牺牲步态稳定的问题。
- 四条腿是否有更清晰的摆腿动作，是否减少拖脚。

训练日志中重点看：

- `Train/mean_arm_reward`
- `Policy/arm_action_mean_abs`
- `Policy/arm_noise_std`
- episode reward 是否继续上升
- 是否出现大量 early termination 或机器人高度过低终止

## 下一步建议

如果继续训练后大臂仍然不展开：

- 进一步提高 `end_effector_forward_tracking.weight`，例如从 `2.0` 增加到 `4.0`。
- 将机械臂 `pos_x` 范围再收窄到更明确的前伸目标，例如 `(0.62, 0.75)`。
- 降低或临时关闭 `end_effector_orientation_tracking`，先让机械臂学会位置跟踪。
- 检查 `joint2`、`joint3` 的正负方向是否符合“向前伸展”的直觉。
- 增加单独的 arm-only debug 输出，打印 command 和 end-effector 实际位置误差。

如果步态仍然不协调：

- 降低线速度上限，先训练更慢的稳定步态。
- 增强 base orientation 和 height reward。
- 调低 action scale，避免腿部动作过大。
- 分阶段训练：先固定较简单的 arm command，再逐渐扩大机械臂目标范围。

