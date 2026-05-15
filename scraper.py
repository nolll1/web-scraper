import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

OUTPUT_JSON = Path(__file__).resolve().parent / "output.json"

ENTERTAINMENT_URL = "https://ekantipur.com/entertainment"
CARTOON_URL = "https://ekantipur.com/cartoon"
BASE_URL = "https://ekantipur.com"


def scrape_first_cartoon() -> dict[str, str | None]:
    """First cartoon on the cartoon page: title (caption), image URL, author if present."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(CARTOON_URL, wait_until="domcontentloaded")

        box = page.locator(".col-lg-4").first

        title = ""
        if box.locator(".cartoon-description > p").count() > 0:
            title = box.locator(".cartoon-description > p").first.inner_text().strip()

        image_url = ""
        if box.locator("img").count() > 0:
            img = box.locator("img").first
            raw_src = img.get_attribute("src") or ""
            if not raw_src.strip():
                raw_src = img.get_attribute("data-src") or ""
            if raw_src.strip():
                image_url = urljoin(BASE_URL, raw_src.strip())

        author: str | None = None
        if box.locator(".author-name").count() > 0:
            author = box.locator(".author-name").first.inner_text().strip() or None

        browser.close()

    return {"title": title, "image_url": image_url, "author": author}


def scrape_ekantipur() -> list[dict[str, str | None]]:
    """Return the top 5 article cards from the Entertainment listing."""
    articles: list[dict[str, str | None]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(ENTERTAINMENT_URL, wait_until="domcontentloaded")

        # On this page the section label is usually one shared .category-name
        # (not repeated inside every card), so we fall back to it when missing.
        section_category = ""
        if page.locator(".category-name").count() > 0:
            section_category = page.locator(".category-name").first.inner_text().strip()

        cards = page.locator("div.category")
        total = min(5, cards.count())

        for i in range(total):
            card = cards.nth(i)

            title = ""
            if card.locator("h2").count() > 0:
                title = card.locator("h2").first.inner_text().strip()

            image_url = ""
            if card.locator("img").count() > 0:
                img = card.locator("img").first
                # Some cards lazy-load: real URL is in data-src until the image loads
                raw_src = img.get_attribute("src") or ""
                if not raw_src.strip():
                    raw_src = img.get_attribute("data-src") or ""
                if raw_src.strip():
                    image_url = urljoin(BASE_URL, raw_src.strip())

            category = section_category
            if card.locator(".category-name").count() > 0:
                category = card.locator(".category-name").first.inner_text().strip()

            author: str | None = None
            if card.locator(".author-name").count() > 0:
                raw_author = card.locator(".author-name").first.inner_text().strip()
                author = raw_author or None

            articles.append(
                {
                    "title": title,
                    "image_url": image_url,
                    "category": category,
                    "author": author,
                }
            )

        browser.close()

    return articles


def scrape_and_save_json(path: Path | None = None) -> Path:
    """Run scrapers and write { entertainment_news, cartoon_of_the_day } to JSON."""
    out = path or OUTPUT_JSON
    payload = {
        "entertainment_news": scrape_ekantipur(),
        "cartoon_of_the_day": scrape_first_cartoon(),
    }
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


if __name__ == "__main__":
    saved = scrape_and_save_json()
    print(f"Wrote {saved}")
