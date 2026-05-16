"""Small diagnostic script to verify arm actions reach joint1..joint6."""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Debug arm action plumbing.")
parser.add_argument("--task", type=str, default="Isaac-Go2Arm-Flat")
parser.add_argument("--num_envs", type=int, default=1)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym
import torch

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import parse_env_cfg

import Go2Arm_Lab.tasks  # noqa: F401


def main():
    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=args_cli.num_envs)
    env = gym.make(args_cli.task, cfg=env_cfg)
    env.reset()

    robot = env.unwrapped.scene["robot"]
    arm_joint_ids, arm_joint_names = robot.find_joints(["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"], preserve_order=True)
    print("[DEBUG] action_space:", env.action_space, flush=True)
    print("[DEBUG] arm_joint_names:", arm_joint_names, flush=True)
    print("[DEBUG] initial arm pos:", robot.data.joint_pos[0, arm_joint_ids].detach().cpu().tolist(), flush=True)

    actions = torch.zeros(env.action_space.shape, device=env.unwrapped.device)
    actions[:, 12:] = 1.0

    for step in range(40):
        env.step(actions)
        if step in (0, 1, 5, 10, 20, 39):
            arm_pos = robot.data.joint_pos[0, arm_joint_ids].detach().cpu().tolist()
            arm_target = env.unwrapped.action_manager.action[0, 12:].detach().cpu().tolist()
            print(f"[DEBUG] step={step:02d} arm_action={arm_target} arm_pos={arm_pos}", flush=True)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
