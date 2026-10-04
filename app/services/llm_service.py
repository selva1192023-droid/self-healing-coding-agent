import ollama


MODEL_NAME = "qwen2.5-coder:3b"


def generate_code(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert software development AI agent. "
                    "Generate clean, correct, and executable code. "
                    "Follow the user's requirements carefully."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response["message"]["content"]