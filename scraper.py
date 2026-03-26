import json
import re
import warnings
from pathlib import Path

import niquests
from lxml import html

URL = 'https://www.bis.gov/regulations/ear/744#supplement-4-744'
OUTPUT_JSON = Path('data.json')
KEYWORDS = (
    'university',
    'institute of science and technology',
    'institute of technology',
    'academy',
    'college',
)


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def text_content(node) -> str:
    return normalize_text(' '.join(node.xpath('.//text()')))


def extract_name(raw: str) -> str:
    name = re.split(r';', raw, maxsplit=1)[0]
    name = re.split(r',\s*a\.k\.a\.?,?', name, maxsplit=1, flags=re.IGNORECASE)[0]
    name = re.split(
        r',\s+(?=(?:No\.|Room\b|Building\b|\d|[A-Z][a-z]+ District|University City|East Campus|West Campus|South Campus|North Campus))',
        name,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return name.strip(' .,')


def is_candidate(raw: str) -> bool:
    lower = raw.lower()
    return 'china' in lower and any(keyword in lower for keyword in KEYWORDS)


def fetch_page() -> str:
    warnings.filterwarnings(
        'ignore', message='Unverified HTTPS request'
    )  # https://community.cloudflare.com/t/cloudflare-ssl-trust-chain-ends-with-invalid-root-ca-aaa-cerificate-services/843576
    session = niquests.Session()
    session.trust_env = False
    response = session.get(
        URL,
        verify=False,
    )
    response.raise_for_status()
    return response.text


def parse_entries(page_html: str) -> list[dict[str, str]]:
    doc = html.fromstring(page_html)
    supplement = doc.get_element_by_id('Supplement-No.-4-to-Part-744')

    entries: list[dict[str, str]] = []

    for item in supplement.xpath('.//li'):
        raw = text_content(item)
        if not raw or not is_candidate(raw):
            continue
        name = extract_name(raw)
        if any(keyword in name.lower() for keyword in KEYWORDS):
            entries.append({'name': name, 'raw': raw})

    current_country = ''
    for row in supplement.xpath('.//tr[td]'):
        cells = row.xpath('./td')
        if len(cells) < 2:
            continue

        country = text_content(cells[0])
        if country:
            current_country = country
        if not current_country.upper().startswith('CHINA'):
            continue

        raw = text_content(cells[1])
        if not raw or not is_candidate(raw):
            continue

        name = extract_name(raw)
        if 'south africa' in name.lower():
            continue
        if any(keyword in name.lower() for keyword in KEYWORDS):
            entries.append({'name': name, 'raw': raw})

    deduped: dict[str, dict[str, str]] = {}
    for entry in entries:
        deduped.setdefault(entry['name'], entry)

    return sorted(deduped.values(), key=lambda entry: entry['name'].casefold())


def main() -> None:
    page_html = fetch_page()
    data = parse_entries(page_html)
    OUTPUT_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'Wrote {len(data)} entries to {OUTPUT_JSON}')


if __name__ == '__main__':
    main()
