
from MAA2C import MAA2C
from common.utils import agg_double_list

import sys
import gym
import numpy as np
import matplotlib.pyplot as plt

import random

import ray
from ray.rllib.env.multi_agent_env import MultiAgentEnv, make_multi_agent
# from ray.rllib.examples.env.multi_agent import MultiAgentCartPole


MAX_EPISODES = 5000
EPISODES_BEFORE_TRAIN = 100
EVAL_EPISODES = 10
EVAL_INTERVAL = 100

# roll out n steps
ROLL_OUT_N_STEPS = 10
# only remember the latest ROLL_OUT_N_STEPS
MEMORY_CAPACITY = ROLL_OUT_N_STEPS
# only use the latest ROLL_OUT_N_STEPS for training A2C
BATCH_SIZE = ROLL_OUT_N_STEPS

REWARD_DISCOUNTED_GAMMA = 0.99
ENTROPY_REG = 0.00
#
DONE_PENALTY = -10.

CRITIC_LOSS = "mse"
MAX_GRAD_NORM = None

EPSILON_START = 0.99
EPSILON_END = 0.05
EPSILON_DECAY = 500

RANDOM_SEED = 2017


def run(env_id="CartPole-v0"):

    env = make_multi_agent(env_id)
    print(env)
    # env.seed(RANDOM_SEED)
    env_eval = make_multi_agent(env_id)
    # env_eval.seed(RANDOM_SEED)
    state_dim = env.observation_space.shape[0]
    if len(env.action_space.shape) > 1:
        action_dim = env.action_space.shape[0]
    else:
        action_dim = env.action_space().n

    maa2c = MAA2C(env=env, n_agents=2, 
              state_dim=state_dim, action_dim=action_dim, memory_capacity=MEMORY_CAPACITY,
              batch_size=BATCH_SIZE, entropy_reg=ENTROPY_REG,
              done_penalty=DONE_PENALTY, roll_out_n_steps=ROLL_OUT_N_STEPS,
              reward_gamma=REWARD_DISCOUNTED_GAMMA,
              epsilon_start=EPSILON_START, epsilon_end=EPSILON_END,
              epsilon_decay=EPSILON_DECAY, max_grad_norm=MAX_GRAD_NORM,
              episodes_before_train=EPISODES_BEFORE_TRAIN,
              critic_loss=CRITIC_LOSS, critic_parameter_sharing=True)

    episodes =[]
    eval_rewards =[]
    while maa2c.n_episodes < MAX_EPISODES:
        maa2c.interact()
        if maa2c.n_episodes >= EPISODES_BEFORE_TRAIN:
            maa2c.train()
        if maa2c.episode_done and ((maa2c.n_episodes+1)%EVAL_INTERVAL == 0):
            rewards, _ = maa2c.evaluation(env_eval, EVAL_EPISODES)
            rewards_mu, rewards_std = agg_double_list(rewards)
            print("Episode %d, Average Reward %.2f" % (maa2c.n_episodes+1, rewards_mu))
            episodes.append(maa2c.n_episodes+1)
            eval_rewards.append(rewards_mu)

    episodes = np.array(episodes)
    eval_rewards = np.array(eval_rewards)
    np.savetxt("./output/%s_maa2c_episodes.txt"%env_id, episodes)
    np.savetxt("./output/%s_maa2c_eval_rewards.txt"%env_id, eval_rewards)

    plt.figure()
    plt.plot(episodes, eval_rewards)
    plt.title("%s"%env_id)
    plt.xlabel("Episode")
    plt.ylabel("Average Reward")
    plt.legend(["maa2c"])
    plt.savefig("./output/%s_maa2c.png"%env_id)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        run(sys.argv[1])
    else:
        run()
