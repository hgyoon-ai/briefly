from pathlib import Path

TIMEZONE = "Asia/Seoul"

DAILY_HOURS = 24
WEEKLY_DAYS = 7
MONTHLY_DAYS = 30

MAX_PER_SOURCE = {
    "rss": 15,
    "github": 40,
    "huggingface": 30,
    "total": 150,
}

RSS_SOURCES = [
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "tab": "ai",
    },
    {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/news/rss.xml",
        "tab": "ai",
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "tab": "ai",
    },
    {
        "name": "Meta AI Blog",
        "url": "https://ai.meta.com/blog/rss/",
        "tab": "ai",
    },
    {
        "name": "Microsoft Research Blog",
        "url": "https://www.microsoft.com/en-us/research/feed/",
        "tab": "ai",
    },
    {
        "name": "NVIDIA Developer Blog",
        "url": "https://developer.nvidia.com/blog/feed/",
        "tab": "ai",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "tab": "ai",
    },
    {
        "name": "PyTorch Blog",
        "url": "https://pytorch.org/feed.xml",
        "tab": "ai",
    },
]

GITHUB_KEYWORDS = [
    "agent",
    "rag",
    "llm",
    "inference",
    "transformer",
    "vector",
    "eval",
    "multimodal",
]

HF_TRENDING_URL = "https://huggingface.co/api/models"

PUBLIC_LATEST_DIR = Path("public/latest")
ARCHIVE_DIR = Path("archive")

ARCHIVE_FILENAME_FORMAT = "{date}_{period}.json"
