import threading
import queue
import subprocess
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

llm_prompt_queue = queue.Queue()

class LLMBackgroundWorker:
    def __init__(self, model_name="tinyllama", max_workers=14):
        self.model_name = model_name
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.thread = threading.Thread(target=self._worker, daemon=True)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
        self.executor.shutdown(wait=True)

    def _worker(self):
        while self.running:
            try:
                # Get an item from the queue (blocking with timeout)
                item = llm_prompt_queue.get(timeout=1)
                if item:
                    # Submit the processing to the thread pool so multiple prompts run concurrently
                    self.executor.submit(self._process_item, item)
            except queue.Empty:
                continue

    def _process_item(self, item):
        try:
            sender, message, user_id = item
            response = self._ask_llm(sender, message)
            self._log_to_db(sender, user_id, message, response)
        finally:
            # Mark the task as done only after processing is complete
            llm_prompt_queue.task_done()

    def _ask_llm(self, sender, message):
        prompt = f"[{sender}] {message}\nRespond with action."
        try:
            result = subprocess.run(
                ["ollama", "run", self.model_name, prompt],
                capture_output=True,
                text=True,
                encoding="utf-8",  # force UTF-8 decoding
                errors="replace",
                timeout=300
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"LLM failed with code {result.returncode}: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "LLM Timeout: Default response triggered. Escalate to caregiver."
        except Exception as e:
            return f"LLM Error: {e}"

    def _log_to_db(self, sender, user_id, message, response):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn = sqlite3.connect("elderly_care.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO agent_communications (sender, user_id,  message, response, timestamp) VALUES (?, ?, ?, ?, ?)",
                (sender, user_id, message, response, timestamp)
            )
            conn.commit()
            conn.close()
            print(f"[LLMWorker] Logged response for [{sender}] into database at {timestamp}.")
        except Exception as e:
            print(f"[LLMWorker] Failed to log to database: {e}")

# Singleton worker instance
llm_worker = LLMBackgroundWorker()
llm_worker.start()
