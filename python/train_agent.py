import os
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from trading_env import LimitOrderBookEnv

def main():
    print("Booting the pipeline/.. ")
    env = LimitOrderBookEnv(max_steps=50000)

    print("Running strict Gymnasium API compliance check...")
    check_env(env, warn=True)
    print("Environment is fully compliant.")



    print("\nInitializing PPO Neural Network...")
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003, batch_size=64, device="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu")
    print("Starting Training Loop. Pumping 1,000,000 steps through the C++ Engine...")
    model.learn(total_timesteps=1_000_000)

    os.makedirs("models", exist_ok=True)
    save_path = os.path.join("models", "ppo_market_maker_v1")
    model.save(save_path)
    print(f"\nTraining Complete. Neural Network saved to: {save_path}.zip")

def evaluate():
    print("Evaluating Trained Agent...")
    env = LimitOrderBookEnv(max_steps=1000)
    model = PPO.load("ppo_quant_market_maker")

    obs, _ = env.reset()
    total_reward = 0

    for i in range(1000):
        # deterministic=True forces the network to pick its best calculated move
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward

        if terminated or truncated:
            break

    print(f"Evaluation Complete. Total Accumulated PnL/Reward: {total_reward}")

if __name__ == "__main__":
    main()



