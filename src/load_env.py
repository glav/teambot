from dotenv import load_dotenv


def load_env():
    """Locate and load .env file, returning load status."""
    env_loaded = load_dotenv()
    print(f"Env variables loaded: {env_loaded}")
    return env_loaded
