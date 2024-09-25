import logging
from fastapi import APIRouter, Depends, Path, Query
import pandas as pd
from openrank_sdk import EigenTrust
import requests
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json

load_dotenv()
router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common configurations
def get_env_vars(prefix=''):
    return {
        'base_url': os.getenv(f'{prefix}BASE_URL'),
        'base_url_pretrust': os.getenv(f'{prefix}BASE_URL_PRETRUST'),
        'database_url': os.getenv(f'DATABASE_URL_{prefix.upper()}'),
    }

def create_db_session(database_url):
    if database_url is None:
        raise ValueError("Database URL is not set in environment variables")
    engine = create_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to config.json (assuming it's in the app directory)
config_path = os.path.join(current_dir, '..', '..', 'config.json')

# Load configuration from JSON file
with open(config_path) as config_file:
    configs = json.load(config_file)

# Remove the subcategory_mapping dictionary

def get_attestations(graphql_url, variables):
    headers = {
        'Content-Type': 'application/json',
    }
    query = """
    query Attestations($where: AttestationWhereInput) {
      attestations(where: $where) {
        attester
        recipient
      }
    }
    """
    payload = {
        'query': query,
        'variables': variables
    }
    try:
        response = requests.post(graphql_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result['data']['attestations']
    except Exception as e:
        logger.error(f"Error fetching attestations: {e}")
        return []

def calculate_scores(config):
    logger.info(f"Calculating scores for config: {config}")

    attestations = get_attestations(config['graphql_url'], config['variables'])
    logger.info(f"Fetched {len(attestations)} attestations")

    localtrust = [{'i': r['attester'].lower(), 'j': r['recipient'].lower(), 'v': 1} for r in attestations if r['attester'] != r['recipient']]
    logger.info(f"Generated {len(localtrust)} localtrust entries")

    pretrust_attestations = get_attestations(config['graphql_url'], config['pretrust_variables'])
    logger.info(f"Fetched {len(pretrust_attestations)} pretrust attestations")

    pretrust = [{'i': r['attester'].lower(), 'j': r['recipient'].lower(), 'v': 2} for r in pretrust_attestations]
    logger.info(f"Generated {len(pretrust)} pretrust entries")

    localtrust_values = {item['i'].lower() for item in localtrust}.union({item['j'].lower() for item in localtrust})
    pretrust = [r for r in pretrust if r['i'] in localtrust_values]
    logger.info(f"Filtered pretrust entries: {len(pretrust)}")
    
    a = EigenTrust(host_url='https://ek-go-eigentrust.k3l.io')
    scores = a.run_eigentrust(localtrust, pretrust)
    logger.info(f"Calculated {len(scores)} scores")
    
    return pd.DataFrame(scores).drop_duplicates(subset='i').to_dict(orient='records')

def update_ranking_table(db, scores):
    try:
        logger.info("Starting to update ranking table")
        db.execute(text('DELETE FROM "Ranking"'))
        db.commit()
        logger.info("Deleted existing rankings")

        sorted_scores = sorted(scores, key=lambda x: x['v'], reverse=True)
        logger.info(f"Inserting {len(sorted_scores)} new rankings")
        for position, score in enumerate(sorted_scores, start=1):
            address, value = score.get('i'), score.get('v')
            if address and value is not None:
                db.execute(
                    text('INSERT INTO "Ranking" (address, value, position) VALUES (:address, :value, :position) '
                         'ON CONFLICT (address) DO UPDATE SET value = :value, position = :position'),
                    {"address": address, "value": value, "position": position},
                )
        db.commit()
        logger.info("Inserted new rankings")

        logger.info("Updating User rankScores")
        for score in sorted_scores:
            address, value = score.get('i'), score.get('v')
            if address and value is not None:
                db.execute(
                    text('UPDATE "User" SET "rankScore" = :value WHERE LOWER("wallet") = LOWER(:address)'),
                    {"value": value, "address": address},
                )
        db.commit()
        logger.info("Updated User rankScores")

    except Exception as e:
        logger.error(f"Error updating ranking table: {e}", exc_info=True)
        db.rollback()

@router.get("/{config_key}")
async def get_rankings(
    config_key: str = Path(..., description="The configuration key to use"),
    limit: int = Query(100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    logger.info(f"Starting get_scores for {config_key}")
    if config_key not in configs:
        return {"error": f"Invalid configuration key: {config_key}"}
    
    config = configs[config_key]
    env_vars = get_env_vars(config_key)
    
    if env_vars['database_url'] is None:
        return {"error": f"Database URL not found for {config_key}"}
    
    try:
        db = create_db_session(env_vars['database_url'])
        scores = calculate_scores(config)
        print(scores)
        update_ranking_table(db, scores)
        logger.info(f"Scores updated successfully for {config_key}")
        return {"message": f"Scores updated successfully for {config_key}"}
    except Exception as e:
        logger.error(f"Error in get_scores for {config_key}: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        if 'db' in locals():
            db.close()
