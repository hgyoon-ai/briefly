from pathlib import Path

TIMEZONE = "Asia/Seoul"

DAILY_HOURS = 24
WEEKLY_DAYS = 7
MONTHLY_DAYS = 30

MAX_RSS_ITEMS = 15
MAX_HF_ITEMS = 30
MAX_TOTAL_ITEMS = 150

MAX_PER_SOURCE = {
  "rss": MAX_RSS_ITEMS,
  "huggingface": MAX_HF_ITEMS,
  "total": MAX_TOTAL_ITEMS,
}

OPENAI_ITEM_MODEL = "gpt-5-mini"
OPENAI_ISSUE_MODEL = "gpt-5.1"
OPENAI_CHECK_MODEL = "gpt-4.1-mini"

OPENAI_ITEM_MODEL_SHORT = "gpt-5-mini"
OPENAI_ITEM_MODEL_LONG = "gpt-5.1"
OPENAI_ITEM_MODEL_THRESHOLD = 600

HF_IMPORTANCE_PENALTY = 2

TOPIC_TAXONOMY = [
  "Models",
  "Training",
  "Inference",
  "Tooling",
  "Infra",
  "Safety",
  "Research",
  "Product",
  "Business",
  "Data",
]

OPENAI_TEMPERATURE_ITEM = None
OPENAI_TEMPERATURE_ISSUE = None
OPENAI_TEMPERATURE_CHECK = None

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
    {
      "name": "Mistral AI Blog",
      "url": "https://mistral.ai/news/rss.xml",
      "tab": "ai",
    },
    {
      "name": "Cohere Blog",
      "url": "https://cohere.com/blog/rss.xml",
      "tab": "ai",
    },
    {
      "name": "Stability AI News",
      "url": "https://stability.ai/news/rss.xml",
      "tab": "ai",
    },
  ]

HF_TRENDING_URL = "https://huggingface.co/api/models"

PUBLIC_LATEST_DIR = Path("public/latest")
ARCHIVE_DIR = Path("archive")

ARCHIVE_FILENAME_FORMAT = "{date}_{period}.json"
