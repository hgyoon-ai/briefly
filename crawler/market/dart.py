import io
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

import requests


CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
LIST_URL = "https://opendart.fss.or.kr/api/list.json"


def normalize_corp_name(name):
    if not name:
        return ""
    lowered = name.lower()
    lowered = re.sub(r"\(주\)|㈜|주식회사", "", lowered)
    lowered = re.sub(r"\s+", "", lowered)
    lowered = re.sub(r"[^a-z0-9가-힣]", "", lowered)
    return lowered


def fetch_corp_codes(api_key):
    response = requests.get(CORP_CODE_URL, params={"crtfc_key": api_key}, timeout=30)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        members = archive.namelist()
        if not members:
            raise RuntimeError("DART corpCode zip is empty")
        with archive.open(members[0]) as file:
            xml_bytes = file.read()

    root = ET.fromstring(xml_bytes)
    corp_entries = []
    for item in root.findall("list"):
        corp_entries.append(
            {
                "corp_code": item.findtext("corp_code"),
                "corp_name": item.findtext("corp_name"),
            }
        )
    return corp_entries


def build_corp_code_map(companies, api_key, overrides=None):
    overrides = overrides or {}
    corp_entries = fetch_corp_codes(api_key)
    normalized = {}
    for entry in corp_entries:
        normalized_name = normalize_corp_name(entry.get("corp_name"))
        if normalized_name:
            normalized.setdefault(normalized_name, []).append(entry)

    result = {}
    unmatched = []
    for name in companies:
        if name in overrides:
            result[name] = overrides[name]
            continue

        key = normalize_corp_name(name)
        candidates = normalized.get(key, [])
        if len(candidates) == 1:
            result[name] = candidates[0]["corp_code"]
            continue
        if not candidates:
            # try contains match
            matches = [
                entry for normalized_name, entries in normalized.items()
                if key and key in normalized_name
                for entry in entries
            ]
            if len(matches) == 1:
                result[name] = matches[0]["corp_code"]
                continue
        unmatched.append(name)

    return result, unmatched


def list_disclosures(
    api_key,
    corp_code,
    start_date,
    end_date,
    *,
    pblntf_ty=None,
    last_reprt_at=None,
):
    """List disclosures for a corp within a date range.

    Notes:
    - OpenDART list.json supports filtering by pblntf_ty (A..J) and last_reprt_at (Y/N).
    - The API accepts a single pblntf_ty per request, so when a list is provided, we fan out
      and merge results.
    """

    def _list_one(p_ty):
        items = []
        page_no = 1
        while True:
            params = {
                "crtfc_key": api_key,
                "corp_code": corp_code,
                "bgn_de": start_date.strftime("%Y%m%d"),
                "end_de": end_date.strftime("%Y%m%d"),
                "page_no": page_no,
                "page_count": 100,
            }
            if p_ty:
                params["pblntf_ty"] = p_ty
            if last_reprt_at:
                params["last_reprt_at"] = last_reprt_at

            response = requests.get(LIST_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") == "013":
                break
            if payload.get("status") != "000":
                raise RuntimeError(f"DART list error: {payload}")

            page_items = payload.get("list", [])
            for entry in page_items:
                # Keep track of which disclosure group this came from for downstream filtering/debug.
                if p_ty:
                    entry["_pblntf_ty"] = p_ty
                items.append(entry)

            total_page = int(payload.get("total_page") or 1)
            if page_no >= total_page:
                break
            page_no += 1
        return items

    if not pblntf_ty:
        return _list_one(None)

    if isinstance(pblntf_ty, (list, tuple, set)):
        merged = []
        for ty in pblntf_ty:
            merged.extend(_list_one(ty))
        return merged

    return _list_one(pblntf_ty)


def build_disclosure_url(rcept_no):
    if not rcept_no:
        return None
    return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"


def parse_rcept_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y%m%d")
