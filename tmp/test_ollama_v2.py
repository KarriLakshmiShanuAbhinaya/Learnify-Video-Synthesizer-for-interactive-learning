import subprocess

def test_ollama():
    topic = "Machine Learning"
    prompt = f"Summarize {topic} in 50 words plain text."
    try:
        print(f"Running ollama with prompt: {prompt}")
        result = subprocess.run(["ollama", "run", "gemma:2b"], input=prompt.encode("utf-8"), capture_output=True, timeout=60)
        print("STDOUT:", result.stdout.decode("utf-8"))
        print("STDERR:", result.stderr.decode("utf-8"))
        print("Return Code:", result.returncode)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ollama()
