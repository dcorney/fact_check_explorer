# See how Google's Fact Check Tools API works
# See https://developers.google.com/fact-check/tools/api/reference/rest/v1alpha1/claims for data structure etc.
import json
from typing import List
import requests
import hashlib

API_KEY = "INSERT YOURS HERE"  # Instructions https://support.google.com/googleapi/answer/6158862
URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
LANGUAGE_CODE = "EN"


def find_publishers(query: str, max_age=30) -> set:
    """Get list of all publishers (e.g. fact checking organizations) that have
    published claims matching the given query in the last *max_age* days.
    """

    data = {
        "query": query,
        "maxAgeDays": max_age,
        "pageSize": 25,
        "languageCode": LANGUAGE_CODE,
        "key": API_KEY,  # NB: API key is passed into params, not headers or auth or anywhere else
    }

    r = requests.get(URL, params=data)
    rj = r.json()

    publishers = set()
    finished = False
    claims = rj.get("claims", [])
    if claims is None or len(claims) == 0:
        finished = True
    while finished is False:
        next_page = rj.get("nextPageToken")
        for c in claims:
            claim_review = c.get("claimReview")[0]
            site = claim_review.get("publisher").get("site")
            publishers.add(site)
        if next_page is None:
            finished = True
        else:
            # Getting next page
            data["pageToken"] = next_page
            r = requests.get(URL, params=data)
            rj = r.json()
            claims = rj.get("claims")
            if claims is None or len(claims) == 0:
                print("No more claims!")
                finished = True

    return publishers


def find_many_publishers():
    all_pubs = set()
    for query in [
        "vaccine",
        "congress",
        "covid",
        "climate",
        "facebook",
        "twitter",
    ]:
        pubs = find_publishers(query, max_age=90)
        all_pubs.update(pubs)
        print(f"After query '{query}', we have {len(all_pubs)} publishers in total")
    return all_pubs


def get_publisher_sightings(publisher_site="fullfact.org", max_age=30) -> List:
    """Get all fact checks from a single publisher up to *max_age* days old."""
    data = {
        "maxAgeDays": max_age,
        "pageSize": 25,
        "languageCode": LANGUAGE_CODE,
        "reviewPublisherSiteFilter": publisher_site,
        "key": API_KEY,  # NB: API key is passed into params, not headers or auth or anywhere else
    }

    r = requests.get(URL, params=data)
    rj = r.json()

    cm_pairs = []
    finished = False
    claims = rj.get("claims", [])
    while finished is False:
        next_page = rj.get("nextPageToken")
        for c in claims:
            claim_review = c.get("claimReview")[0]
            fce_claim_text = claim_review.get("title")
            fce_sighting = c.get("text")

            publisher = claim_review.get("publisher").get(
                "name", claim_review.get("publisher").get("site", "na")
            )
            # FCE doesn't give claim ids, so let's make one by hashing the organzation, review URL & date
            raw_id = " ".join(
                [
                    publisher,
                    claim_review.get("url"),
                    claim_review.get("reviewDate", ""),
                ]
            )
            claim_id = hashlib.sha256(raw_id.encode()).hexdigest()
            cm_pairs.append(
                {
                    "claim_id": claim_id,
                    "claim_org": publisher,
                    "claim_text": fce_claim_text,
                    "claim_conclusion": claim_review.get("textualRating"),
                    "claim_url": claim_review.get("url"),
                    "text": fce_sighting,
                    "publication": c.get("claimant"),
                    "publication_date": c.get("claimDate"),
                }
            )

        if next_page is None:
            finished = True
        else:
            # Getting next page of results
            data["pageToken"] = next_page
            r = requests.get(URL, params=data)
            rj = r.json()

            claims = rj.get("claims")

    return cm_pairs


def recent_sample(publishers: set, output_filename="fce_sightings.json") -> dict:
    """Find recent sightings from each of a set of publishers (fact checkers).
    Optionally write them to a file.
    Also display how many sightings were found per publisher.
    """
    site_counts = {}
    all_pairs = {}

    for pub in publishers:
        pairs = get_publisher_sightings(publisher_site=pub)
        print(f"Got {len(pairs):4d} claim-sentence pairs from {pub:30s}")
        for p in pairs:
            hash_key = hashlib.sha256(
                " ".join([p.get("text"), p.get("claim_text")]).encode()
            ).hexdigest()
            all_pairs[hash_key] = p
        site_counts[pub] = len(pairs)

    print(site_counts)

    if output_filename is not None:
        with open(output_filename, "w") as fout:
            fout.write(json.dumps(all_pairs))

    return all_pairs


if __name__ == "__main__":
    all_pubs = find_many_publishers()
    claim_match_pairs = recent_sample(all_pubs)
    # Or try this to focus on one org:
    # claim_match_pairs = get_publisher_sightings("fullfact.org")
    print(claim_match_pairs)
