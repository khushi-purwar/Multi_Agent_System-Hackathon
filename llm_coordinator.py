import subprocess

class LLMCoordinator:
    def __init__(self, model_name="llama3"):
        self.model_name = model_name

    def ask(self, sender, message):
        prompt = f"[{sender}] needs help: {message}\nRespond with what action should be taken."
        try:
            result = subprocess.run(
                ["ollama", "run", self.model_name, prompt],
                capture_output=True, text=True, timeout=20
            )
            return result.stdout.strip()
        except Exception as e:
            return f"LLM Error: {e}"
