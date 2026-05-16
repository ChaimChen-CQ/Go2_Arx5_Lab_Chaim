"""Debug a policy checkpoint in play mode by printing commands, velocities, and actions."""

import argparse
import os
import sys

from isaaclab.app import AppLauncher

import cli_args  # isort: skip

parser = argparse.ArgumentParser(description="Debug RSL-RL play tracking.")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--task", type=str, default="Isaac-Go2Arm-Flat-Play")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point")
parser.add_argument("--steps", type=int, default=80)
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import gymnasium as gym
import torch

from local_rsl_rl.runners import OnPolicyRunner
from local_rsl_rl.wrappers import RslRlVecEnvWrapper

from isaaclab.envs import DirectMARLEnv, DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg, multi_agent_to_single_agent
from isaaclab.utils.assets import retrieve_file_path

from Go2Arm_Lab.tasks.manager_based.go2arm_lab.config.agents import Go2ArmRslRlOnPolicyRunnerCfg

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

import Go2Arm_Lab.tasks  # noqa: F401


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: Go2ArmRslRlOnPolicyRunnerCfg):
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    env_cfg.scene.num_envs = args_cli.num_envs if args_cli.num_envs is not None else env_cfg.scene.num_envs
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device

    log_root_path = os.path.abspath(os.path.join("logs", "rsl_rl", agent_cfg.experiment_name))
    resume_path = retrieve_file_path(args_cli.checkpoint) if args_cli.checkpoint else get_checkpoint_path(
        log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint
    )

    env = gym.make(args_cli.task, cfg=env_cfg)
    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(resume_path)
    policy = runner.get_inference_policy(device=env.unwrapped.device)

    obs, _ = env.get_observations()
    obs = runner.change_obs_order(obs)
    robot = env.unwrapped.scene["robot"]

    print(f"[DEBUG] checkpoint: {resume_path}", flush=True)
    for step in range(args_cli.steps):
        with torch.inference_mode():
            actions = policy(obs, hist_encoding=False)
            obs, _, _, _, _ = env.step(actions)
            obs = runner.change_obs_order(obs)
        if step % 10 == 0 or step == args_cli.steps - 1:
            cmd = env.unwrapped.command_manager.get_command("base_velocity")[0].detach().cpu().tolist()
            vel = robot.data.root_lin_vel_b[0, :2].detach().cpu().tolist()
            yaw = robot.data.root_ang_vel_b[0, 2].detach().cpu().item()
            act = actions[0].detach().cpu()
            print(
                "[DEBUG] "
                f"step={step:03d} cmd={cmd} vel_xy={vel} yaw_vel={yaw:.3f} "
                f"leg_abs={act[:12].abs().mean().item():.4f} arm_abs={act[12:].abs().mean().item():.4f} "
                f"leg={act[:12].tolist()} arm={act[12:].tolist()}",
                flush=True,
            )

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
