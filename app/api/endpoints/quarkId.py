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
        raw_data = data.get('rawData', {})
        holder_did = raw_data.get('holderDID')
        verifiable_credentials = raw_data.get('verifiableCredentials', [])
        if verifiable_credentials and isinstance(verifiable_credentials, list):
            # Extract the first item if it exists
            first_credential = verifiable_credentials[0]
            credential_subject = first_credential.get('credentialSubject', {})
            proof_value = first_credential.get('proof', {}).get('proofValue')
        else:
            credential_subject = {}
            proof_value = None

        ticket_type = credential_subject.get('category')

        # Debugging logs
        print("invitationId:", invitation_id)
        print("holderDID:", holder_did)
        print("verifiable_credentials:", verifiable_credentials)
        print("credentialSubject:", credential_subject)
        print("ticketType:", ticket_type)
        print("proofValue:", proof_value)

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
                INSERT INTO "Quarkid" ("invitationId", "holderDID", "ticketType", "proofValue", "userId")
                VALUES (:invitationId, :holderDID, :ticketType, :proofValue, :userId)
                '''),
                {
                    "invitationId": invitation_id,
                    "holderDID": holder_did,
                    "ticketType": ticket_type,
                    "proofValue": proof_value,
                    "userId": invitation_id  # Update this if userId should be different
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
