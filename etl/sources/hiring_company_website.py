from __future__ import annotations

import datetime as dt

from sources.base import HiringSource, json_dumps_compact
from sources.http import fetch_html, to_soup
from sources.types import HiringSnapshot
from lib.utils import extract_keywords, extract_job_count


class CompanyWebsiteSource(HiringSource):
    channel = 'company_website'

    def fetch(self, company: dict, run_date: dt.date) -> HiringSnapshot | None:
        url = None
        aliases = company.get('aliases') or ''
        for part in str(aliases).split('|'):
            part = part.strip()
            if part.lower().startswith('url:'):
                url = part[4:].strip()
                break
        if not url:
            return None

        try:
            fr = fetch_html(url)
            soup = to_soup(fr.text)
            text = soup.get_text('\n', strip=True)

            keywords = extract_keywords([text])
            job_count = extract_job_count(text)

            raw = {
                'final_url': fr.final_url,
                'status_code': fr.status_code,
            }

            return HiringSnapshot(
                company_id=int(company['id']),
                snapshot_date=run_date,
                channel=self.channel,
                open_jobs_count=job_count,
                categories=[],
                keywords=keywords,
                source_url=fr.final_url,
                raw_payload=json_dumps_compact(raw),
                confidence=0.400,
            )
        except Exception as e:
            print(f'Failed to fetch {url}: {e}')
            return None
