from dotenv import find_dotenv, load_dotenv

from crawler.config import OPENAI_CHECK_MODEL, OPENAI_TEMPERATURE_CHECK
from crawler.llm.openai_client import call_openai


def main():
    load_dotenv(find_dotenv())
    model = OPENAI_CHECK_MODEL
    response, error = call_openai(
        messages=[
            {"role": "system", "content": "Reply with a short greeting."},
            {"role": "user", "content": "Say hello in one short sentence."},
        ],
        model=model,
        temperature=OPENAI_TEMPERATURE_CHECK,
    )
    if error or response is None:
        print(f"[check] FAILED: {error}")
        return

    content = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    print("[check] OK")
    print(f"[check] model: {model}")
    print(f"[check] response: {content.strip()}")
    if usage:
        print(
            "[check] tokens: "
            f"prompt={usage.prompt_tokens} completion={usage.completion_tokens} "
            f"total={usage.total_tokens}"
        )


if __name__ == "__main__":
    main()
