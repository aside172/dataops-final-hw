import os

import mlflow
from mlflow.genai import register_prompt


TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
PROMPT_NAME = os.getenv("MLFLOW_PROMPT_NAME", "credit-risk-system-prompt")

PROMPTS = [
    "Ты ML-сервис оценки кредитного риска. Верни краткий вывод на русском языке.",
    "Ты ML-сервис оценки кредитного риска. Верни краткий вывод на русском языке и добавь one-line justification.",
    "Ты ML-сервис оценки кредитного риска. Отвечай строго в JSON с полями summary и action.",
]


def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    for prompt in PROMPTS:
        version = register_prompt(name=PROMPT_NAME, template=prompt)
        print(f"Registered prompt version: {version}")


if __name__ == "__main__":
    main()
