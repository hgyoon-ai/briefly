from pathlib import Path

TIMEZONE = "Asia/Seoul"

DAILY_HOURS = 24
WEEKLY_DAYS = 7
MONTHLY_DAYS = 30

MAX_RSS_ITEMS = 15
MAX_HF_ITEMS = 30
MAX_TOTAL_ITEMS = 150
MAX_HN_ITEMS = 15

MAX_PER_SOURCE = {
  "rss": MAX_RSS_ITEMS,
  "huggingface": MAX_HF_ITEMS,
  "hn": MAX_HN_ITEMS,
  "total": MAX_TOTAL_ITEMS,
}

OPENAI_ITEM_MODEL = "gpt-5-mini"
OPENAI_ISSUE_MODEL = "gpt-5.1"
OPENAI_CHECK_MODEL = "gpt-4.1-mini"

OPENAI_ITEM_MODEL_SHORT = "gpt-5-mini"
OPENAI_ITEM_MODEL_LONG = "gpt-5.1"
OPENAI_ITEM_MODEL_THRESHOLD = 600

HF_IMPORTANCE_PENALTY = 2

TABS = ["ai", "finance", "semiconductor", "ev"]

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

SEMICONDUCTOR_TAXONOMY = [
    "Earnings",
    "Demand",
    "Manufacturing",
    "Policy",
    "Investment",
    "Competition",
    "Roadmap",
]

EV_TAXONOMY = [
    "Earnings",
    "Demand",
    "Manufacturing",
    "Policy",
    "Investment",
    "Competition",
    "Roadmap",
]

FINANCE_TAXONOMY = [
    "Regulation",
    "Enforcement",
    "Privacy",
    "Security",
    "Fintech",
    "Payments",
    "Crypto",
    "Compliance",
    "MarketInfra",
    "Policy",
]

TOPIC_TAXONOMY_BY_TAB = {
    "ai": TOPIC_TAXONOMY,
    "finance": FINANCE_TAXONOMY,
    "semiconductor": SEMICONDUCTOR_TAXONOMY,
    "ev": EV_TAXONOMY,
}

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
    {
        "name": "Samsung Newsroom",
        "url": "https://news.samsung.com/global/feed",
        "tab": "semiconductor",
    },
    {
        "name": "SK hynix Newsroom",
        "url": "https://news.skhynix.com/feed/",
        "tab": "semiconductor",
    },
    {
        "name": "Samsung Semiconductor Newsroom",
        "url": "https://news.samsungsemi.com/global/feed/",
        "tab": "semiconductor",
    },
    {
        "name": "SEMI News",
        "url": "https://www.semi.org/en/rss",
        "tab": "semiconductor",
    },
    {
        "name": "EE Times",
        "url": "https://www.eetimes.com/feed/",
        "tab": "semiconductor",
    },
    {
        "name": "TechInsights",
        "url": "https://www.techinsights.com/rss.xml",
        "tab": "semiconductor",
    },
    {
        "name": "Tesla Blog",
        "url": "https://www.tesla.com/blog/rss",
        "tab": "ev",
    },
    {
        "name": "Tesla Investor Relations",
        "url": "https://ir.tesla.com/press-releases/rss.xml",
        "tab": "ev",
    },
    {
        "name": "NHTSA Recalls",
        "url": "https://www.nhtsa.gov/feeds/recalls.xml",
        "tab": "ev",
    },
    {
        "name": "Electrek",
        "url": "https://electrek.co/feed/",
        "tab": "ev",
    },
    {
        "name": "InsideEVs",
        "url": "https://insideevs.com/rss/news/",
        "tab": "ev",
    },
    {
        "name": "Reuters Tesla",
        "url": "https://feeds.reuters.com/reuters/companyNews?format=xml&company=TSLA.O",
        "tab": "ev",
    },

    # Korea-focused finance/regulation/security signals (minimal allowlist).
    {
        "name": "정책브리핑",
        "url": "https://www.korea.kr/rss/policy.xml",
        "tab": "finance",
    },
    {
        "name": "매일경제(증권)",
        "url": "https://www.mk.co.kr/rss/50200011/",
        "tab": "finance",
    },
    {
        "name": "보안뉴스",
        "url": "http://www.boannews.com/media/news_rss.xml",
        "tab": "finance",
    },
    {
        "name": "벤처스퀘어",
        "url": "https://www.venturesquare.net/feed",
        "tab": "finance",
    },
]

HF_TRENDING_URL = "https://huggingface.co/api/models"

HN_API_URL = "https://hn.algolia.com/api/v1/search"
HN_WINDOW_HOURS = 24
HN_POINTS_MIN = 30
HN_COMMENTS_MIN = 20

GITHUB_API_URL = "https://api.github.com"
GITHUB_SEARCH_DAYS = 7
GITHUB_SEARCH_MIN_STARS = 50
GITHUB_SEARCH_PAGES = 2
GITHUB_SEARCH_PER_PAGE = 30
GITHUB_RELEASE_DAYS = 7
DEVELOPER_MAX_CLUSTERS = 20

PUBLIC_LATEST_DIR = Path("public/industry")
ARCHIVE_DIR = Path("archive")

ARCHIVE_FILENAME_FORMAT = "{date}_{period}.json"
