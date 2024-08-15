from fastapi import APIRouter
import pandas as pd
from openrank_sdk import EigenTrust
import requests

router = APIRouter()

def get_attestations(base_url, page=1):
    results = []

    def run(page):
        nonlocal results
        url = base_url
        if page > 1:
            url += f'&page={page}'

        res = requests.get(url).json()
        results.extend(res['attestations'])

        if len(results) < res['totalAttestationCount']:
            return run(page + 1)

        return results

    return run(page)

def calculate_scores():
    base_url = 'https://base-sepolia.easscan.org/attestations/forSchema/0x5ee00c7a6606190e090ea17749ec77fe23338387c23c0643c4251380f37eebc3?_data=routes%2F__boundary%2Fattestations%2FforSchema%2F%24schemaUID&limit=50'
    attestations = get_attestations(base_url)
    localtrust = [{'i': r['attester'].lower(), 'j': r['recipient'].lower(), 'v': 1 } for r in attestations if r['attester'] != r['recipient']]

    base_url_preturst = 'https://base-sepolia.easscan.org/attestations/forSchema/0x9075dee7661b8b445a2f0caa3fc96223b8cc2593c796c414aed93f43d022b0f9?_data=routes%2F__boundary%2Fattestations%2FforSchema%2F%24schemaUID&limit=50'
    attestationszupass = get_attestations(base_url_preturst)
    pretrust = [{'i': r['attester'].lower(), 'j': r['recipient'].lower(), 'v': 1 } for r in attestationszupass]

    # Filter pretrust
    localtrust_values = {item['i'].lower() for item in localtrust}.union({item['j'].lower() for item in localtrust})
    pretrust = [r for r in pretrust if r['i'] in localtrust_values and r['v'] > 0]
    
    a = EigenTrust()
    scores = a.run_eigentrust(localtrust, pretrust)
    result = pd.DataFrame(scores)

    return result.to_dict(orient='records')

@router.get("/")
async def get_scores():
    scores = calculate_scores()
    return {"scores": scores}