# agents/base_agent.py
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from llm_queue_worker import llm_prompt_queue

class BaseAgent:
    def __init__(self, name: str, enable_llm=True):
        self.name = name
        self.enable_llm = enable_llm
        self.executor = ThreadPoolExecutor(max_workers=5)

    def log_to_llm(self, message: str, user_id: str = "unknown"):
        if not self.enable_llm:
            print(f"[{self.name}] Skipping LLM log: {message}")
            return

        def queue_task():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            llm_prompt_queue.put((self.name, message, user_id))
        self.executor.submit(queue_task)

    def shutdown(self):
        self.executor.shutdown(wait=True)
