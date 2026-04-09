from datetime import datetime

def create_outpass_request(student_id, reason, from_time, to_time):
    return {
        "studentId": student_id,
        "reason": reason,

        # Validity window (round trip)
        "fromTime": from_time,      # Out time
        "toTime": to_time,          # Expected return time

        # Status
        "status": "pending",        # pending | approved | rejected

        # QR scan tracking
        "scannedExit": False,       # student left campus
        "scannedEntry": False,      # student returned

        "exitTime": None,
        "entryTime": None,

        # Metadata
        "createdAt": datetime.utcnow(),
        "updatedAt": None
    }
