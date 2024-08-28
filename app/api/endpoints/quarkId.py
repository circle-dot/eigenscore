from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import sessionmaker, Session
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

        invitation_id = data.get('invitationId')
        holder_did = data.get('holderDID')
        ticket_type = data.get('ticketType')
        proof_value = data.get('proofValue')

        if not invitation_id:
            raise HTTPException(status_code=400, detail="invitationId is required")
        if not holder_did:
            raise HTTPException(status_code=400, detail="holderDID is required")
        if not ticket_type:
            raise HTTPException(status_code=400, detail="ticketType is required")

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
    except HTTPException as e:
        print(f"HTTPException: {str(e.detail)}")  # Log specific HTTP error details
        raise
    except Exception as e:
        print("Error processing request:", str(e))  # Log error
        raise HTTPException(status_code=400, detail=f"Error processing request: {str(e)}")
