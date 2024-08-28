from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import sessionmaker, Session  # Ensure Session is imported
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create SQLAlchemy engine and session
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.post("/")
async def submit_data(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        print("Received data:", data)  # Log received data

        # Check if 'rawData' is part of the incoming data
        raw_data = data.get('rawData', {})
        invitation_id = raw_data.get('invitationId')
        holder_did = raw_data.get('holderDID')
        ticket_type = raw_data.get('credentialSubject', {}).get('category')
        proof_value = raw_data.get('verifiableCredentials', [{}])[0].get('proof', {}).get('proofValue')

        if not invitation_id or not holder_did or not ticket_type:
            raise HTTPException(status_code=400, detail="invitationId, holderDID, and ticketType are required")

        # Insert data into the QuarkId table
        try:
            db.execute(
                text('''
                INSERT INTO "QuarkId" (invitationId, holderDID, ticketType, proofValue)
                VALUES (:invitationId, :holderDID, :ticketType, :proofValue)
                ON CONFLICT (invitationId, holderDID) 
                DO UPDATE SET ticketType = EXCLUDED.ticketType, proofValue = EXCLUDED.proofValue
                '''),
                {
                    "invitationId": invitation_id,
                    "holderDID": holder_did,
                    "ticketType": ticket_type,
                    "proofValue": proof_value
                }
            )
            db.commit()
        except Exception as e:
            print("Error inserting data into QuarkId:", str(e))  # Log error
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error inserting data into QuarkId: {str(e)}")

        return {"message": "Data received and inserted successfully"}
    except Exception as e:
        print("Error processing request:", str(e))  # Log error
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")
