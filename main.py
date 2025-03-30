from db import init_db
from agents.run_agent import RunAgent

if __name__ == "__main__":
    #  run only once
    init_db()
    agent_runner = RunAgent()
    agent_runner.run_agents()
    print("✅ All agents have finished processing and saved to the database.")