from fastapi import APIRouter
import pandas as pd
from openrank_sdk import EigenTrust
import requests
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy import func

load_dotenv() 
router = APIRouter()
base_url = os.getenv('BASE_URL')
base_url_pretrust = os.getenv('BASE_URL_PRETRUST')

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    
    # Convert to DataFrame and drop duplicates based on the 'i' column, we could consider doing a filter in pretrust rn, but in the future if we change to have 1 attestation per ticket, we should check it
    result = pd.DataFrame(scores).drop_duplicates(subset='i')

    return result.to_dict(orient='records')


def update_ranking_table():
    db = SessionLocal()
    try:
        print("Deleting old data...")
        db.execute(text('DELETE FROM "Ranking"'))
        db.commit()

        print("Inserting new scores...")
        scores = calculate_scores()

        # Calculate rankings
        sorted_scores = sorted(scores, key=lambda x: x['v'], reverse=True)
        for position, score in enumerate(sorted_scores, start=1):
            address = score.get('i')
            value = score.get('v')
            if address and value is not None:
                try:
                    db.execute(
                        text('''
                        INSERT INTO "Ranking" (address, value, position) 
                        VALUES (:address, :value, :position)
                        ON CONFLICT (address) 
                        DO UPDATE SET value = :value, position = :position
                        '''),
                        {"address": address, "value": value, "position": position},
                    )
                except Exception as e:
                    print(f"Error inserting data: {e}")
                    db.rollback()
        db.commit()
        print("Data updated successfully.")
    except Exception as e:
        print(f"Error updating ranking table: {e}")
        db.rollback()
    finally:
        db.close()


@router.get("/")
async def get_scores():
    update_ranking_table()
    return {"message": "Scores updated successfully"}

