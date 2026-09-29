from googlenewsdecoder import gnewsdecoder


def is_google_news_url(url: str) -> bool:
    return "news.google.com" in url


def decode_google_news_url(url: str) -> str:
    """Resolve a Google News redirect link to the publisher's article URL.

    Never raises: on any failure the original URL is returned unchanged.
    """
    try:
        decoded = gnewsdecoder(url, interval=1)
    except Exception as exc:
        print(f"Exception decoding URL {url}: {exc}")

        return url

    if decoded.get("success") or decoded.get("status"):
        return decoded["decoded_url"]

    print(f"Error decoding URL {url}: {decoded.get('message')}")

    return url
