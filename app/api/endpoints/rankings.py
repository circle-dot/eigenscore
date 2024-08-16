from fastapi import APIRouter
import pandas as pd
from openrank_sdk import EigenTrust
import requests
import os
from dotenv import load_dotenv

load_dotenv() 
router = APIRouter()
base_url = os.getenv('BASE_URL')
base_url_pretrust = os.getenv('BASE_URL_PRETRUST')

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
    attestations = get_attestations(base_url)
    localtrust = [{'i': r['attester'].lower(), 'j': r['recipient'].lower(), 'v': 1 } for r in attestations if r['attester'] != r['recipient']]

    attestationszupass = get_attestations(base_url_pretrust)
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