from fastapi import APIRouter
import pandas as pd
from openrank_sdk import EigenTrust
import requests
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv() 
router = APIRouter()
base_url = os.getenv('BASE_URL')
base_url_pretrust = os.getenv('BASE_URL_PRETRUST')

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Mapping of bytes32 subcategory to assigned values
subcategory_mapping = {
    "0x5374617274757000000000000000000000000000000000000000000000000000": 40,  # Startup
    "0x537065616b657200000000000000000000000000000000000000000000000000": 80,  # Speaker
    "0x696e766974656500000000000000000000000000000000000000000000000000": 60,  # Invite
    "0x43726563696d69656e746f207465616d00000000000000000000000000000000": 100, # Crecimiento team
    "0x53706f6e736f7200000000000000000000000000000000000000000000000000": 40,  # Sponsor
    "0x4275696c64657200000000000000000000000000000000000000000000000000": 40,  # Builder
    "0x566f6c756e746565720000000000000000000000000000000000000000000000": 30,  # Volunteer
    "0x47656e6572616c00000000000000000000000000000000000000000000000000": 20   # General
}

# Define the bytes32 value for "Aleph"
ALEPH_CATEGORY_BYTES32 = "0x416c657068000000000000000000000000000000000000000000000000000000"  # Aleph

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
    if attestationszupass:
        print("First child of attestationszupass:", attestationszupass[0])
    
    pretrust = []
    for r in attestationszupass:
        # Extract subcategory and category from decodedDataJson
        decoded_data = eval(r['decodedDataJson'])  # Assume decodedDataJson is a stringified list of dictionaries
        
        subcategory_bytes32 = next((item['value']['value'] for item in decoded_data if item['name'] == 'subcategory'), None)
        category_bytes32 = next((item['value']['value'] for item in decoded_data if item['name'] == 'category'), None)

        # Filter by "Aleph" category
        if category_bytes32 == ALEPH_CATEGORY_BYTES32:
            if subcategory_bytes32:
                v_value = subcategory_mapping.get(subcategory_bytes32, 1)  # Default to 1 if not found
                pretrust.append({'i': r['attester'].lower(), 'j': r['recipient'].lower(), 'v': v_value })

    # Filter pretrust
    localtrust_values = {item['i'].lower() for item in localtrust}.union({item['j'].lower() for item in localtrust})
    pretrust = [r for r in pretrust if r['i'] in localtrust_values and r['v'] > 0]
    
    a = EigenTrust()
    scores = a.run_eigentrust(localtrust, pretrust)
    
    # Convert to DataFrame and drop duplicates based on the 'i' column
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
