import subprocess

def test_ollama():
    prompt = "Hello"
    try:
        print("Running ollama...")
        result = subprocess.run(["ollama", "run", "gemma:2b"], input=prompt.encode("utf-8"), capture_output=True, timeout=30)
        print("STDOUT:", result.stdout.decode("utf-8"))
        print("STDERR:", result.stderr.decode("utf-8"))
        print("Return Code:", result.returncode)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ollama()
