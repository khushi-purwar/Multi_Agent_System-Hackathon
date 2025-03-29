import subprocess

class OllamaLLM:
    def __init__(self, model="mistral"):
        self.model = model

    def query(self, prompt):
        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt.encode(), capture_output=True, timeout=30
            )
            return result.stdout.decode()
        except Exception as e:
            return f"[ERROR calling Ollama]: {e}"
