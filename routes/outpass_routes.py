from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.mongo import db
from models.outpass_model import create_outpass_request
from bson import ObjectId
from datetime import datetime
import qrcode
import json
import base64
from io import BytesIO

outpass_bp = Blueprint("outpass", __name__)
requests_collection = db["outpass_requests"]
users_collection = db["users"]

# ----------------------------
# Helper: Format MongoDB Docs for JSON
# ----------------------------
def format_outpass(doc):
    """Converts ObjectIds and Datetimes to JSON-serializable formats."""
    if not doc: return None
    doc["_id"] = str(doc["_id"])
    # Convert all possible datetime fields
    date_fields = ["createdAt", "updatedAt", "fromTime", "toTime", "exitTime", "entryTime"]
    for field in date_fields:
        if isinstance(doc.get(field), datetime):
            doc[field] = doc[field].isoformat()
    return doc

# ----------------------------
# Student: Submit Outpass Request
# ----------------------------
@outpass_bp.route("/request", methods=["POST"])
@jwt_required()
def submit_request():
    try:
        data = request.get_json(force=True)
        student_id = get_jwt_identity()

        reason = data.get("reason")
        from_time = data.get("fromTime")
        to_time = data.get("toTime")

        if not reason or not from_time or not to_time:
            return jsonify({"msg": "All fields are required"}), 400

        # Use your model helper to create the dictionary
        request_doc = create_outpass_request(student_id, reason, from_time, to_time)
        
        # Ensure times are stored as datetime objects for proper logic later
        if isinstance(request_doc.get("fromTime"), str):
            request_doc["fromTime"] = datetime.fromisoformat(request_doc["fromTime"].replace("Z", ""))
        if isinstance(request_doc.get("toTime"), str):
            request_doc["toTime"] = datetime.fromisoformat(request_doc["toTime"].replace("Z", ""))
            
        requests_collection.insert_one(request_doc)
        return jsonify({"msg": "Request submitted successfully"}), 201
    except Exception as e:
        return jsonify({"msg": "Error submitting request", "error": str(e)}), 500

# ----------------------------
# Student: Get All Requests (Status Tracking)
# ----------------------------
@outpass_bp.route("/status", methods=["GET"])
@jwt_required()
def get_student_requests():
    try:
        student_id = get_jwt_identity()
        requests = list(requests_collection.find({"studentId": student_id}).sort("createdAt", -1))
        return jsonify({"requests": [format_outpass(r) for r in requests]}), 200
    except Exception as e:
        return jsonify({"msg": "Error fetching requests", "error": str(e)}), 500

# ----------------------------
# Student: Get My Current QR
# ----------------------------
@outpass_bp.route("/my_qr", methods=["GET"])
@jwt_required()
def my_qr():
    try:
        student_id = get_jwt_identity()
        outpass = requests_collection.find_one({
            "studentId": student_id,
            "status": "approved",
            "scannedEntry": False
        })

        if not outpass or "qrCode" not in outpass:
            return jsonify({"msg": "No approved outpass or QR available"}), 404

        return jsonify({
            "id": str(outpass["_id"]),
            "qrCode": outpass["qrCode"],
            "toTime": outpass["toTime"].isoformat() if isinstance(outpass["toTime"], datetime) else outpass["toTime"]
        }), 200
    except Exception as e:
        return jsonify({"msg": "Error fetching QR", "error": str(e)}), 500

# ----------------------------
# Student: Get Active Outpasses (Currently Out)
# ----------------------------
@outpass_bp.route("/active", methods=["GET"])
@jwt_required()
def get_active_outpasses():
    try:
        student_id = get_jwt_identity()
        active_outpasses = list(requests_collection.find({
            "studentId": student_id,
            "status": "approved",
            "scannedExit": True,
            "scannedEntry": False
        }))
        return jsonify({"active_outpasses": [format_outpass(r) for r in active_outpasses]}), 200
    except Exception as e:
        return jsonify({"msg": "Error fetching active outpasses", "error": str(e)}), 500

# ----------------------------
# Student: Get Only Approved Outpasses
# ----------------------------
@outpass_bp.route("/student/approved", methods=["GET"])
@jwt_required()
def get_approved_outpasses():
    try:
        student_id = get_jwt_identity()
        approved = list(requests_collection.find({"studentId": student_id, "status": "approved"}))
        return jsonify({"approved_outpasses": [format_outpass(r) for r in approved]}), 200
    except Exception as e:
        return jsonify({"msg": "Error fetching approved outpasses", "error": str(e)}), 500

# ----------------------------
# Warden: Approve or Reject a Request
# ----------------------------
@outpass_bp.route("/update_status/<request_id>", methods=["PATCH"])
@jwt_required()
def update_request_status(request_id):
    try:
        data = request.get_json(force=True)
        status = data.get("status")
        if status not in ["approved", "rejected"]:
            return jsonify({"msg": "Invalid status"}), 400

        outpass = requests_collection.find_one({"_id": ObjectId(request_id)})
        if not outpass:
            return jsonify({"msg": "Request not found"}), 404

        update_data = {"status": status, "updatedAt": datetime.utcnow()}

        if status == "approved":
            qr_payload = {"id": str(outpass["_id"]), "studentId": str(outpass["studentId"])}
            qr = qrcode.make(json.dumps(qr_payload))
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            update_data["qrCode"] = base64.b64encode(buffer.getvalue()).decode()

        requests_collection.update_one({"_id": ObjectId(request_id)}, {"$set": update_data})
        return jsonify({"msg": f"Request {status} successfully"}), 200
    except Exception as e:
        return jsonify({"msg": "Error updating request", "error": str(e)}), 500

# ----------------------------
# Warden: Get All Student Requests
# ----------------------------
@outpass_bp.route("/all_requests", methods=["GET"])
@jwt_required()
def get_all_requests():
    try:
        requests = list(requests_collection.find().sort("createdAt", -1))
        formatted_requests = []

        for r in requests:
            student_name = "Unknown"

            if r.get("studentId"):
                user = users_collection.find_one(
                    {"_id": ObjectId(r["studentId"])},
                    {"username": 1}
                )
                if user:
                    student_name = user.get("username", "Unknown")

            outpass = format_outpass(r)
            outpass["studentName"] = student_name

            formatted_requests.append(outpass)

        return jsonify({"requests": formatted_requests}), 200

    except Exception as e:
        return jsonify({
            "msg": "Error fetching all requests",
            "error": str(e)
        }), 500


# ----------------------------
# Security: Verify QR (Exit/Entry)
# ----------------------------
# ----------------------------
# Security: Verify QR (Exit/Entry)
# ----------------------------
@outpass_bp.route("/verify_qr", methods=["POST"])
def verify_qr():
    try:
        data = request.get_json(force=True)
        request_id = data.get("id")
        student_id = data.get("studentId")

        outpass = requests_collection.find_one({
            "_id": ObjectId(request_id),
            "studentId": student_id,
            "status": "approved"
        })

        if not outpass:
            return jsonify({"msg": "Outpass not found or not approved"}), 404

        scan_time = datetime.utcnow()
        from_time = outpass["fromTime"]
        to_time = outpass["toTime"]

        # ---------------------------------------------------------
        # 🚪 CASE 1: EXIT SCAN (Student is leaving campus)
        # ---------------------------------------------------------
        if not outpass.get("scannedExit"):
            # 1. Too Early?
            if scan_time.date() < from_time.date():
                return jsonify({"msg": f"Valid only from {from_time.date()}"}), 400
            
            # 2. Too Late to Leave? (Deadline crossed before they even left)
            if scan_time > to_time:
                return jsonify({"msg": "QR Expired: You missed your exit window."}), 403
            
            requests_collection.update_one(
                {"_id": ObjectId(request_id)},
                {"$set": {"scannedExit": True, "exitTime": scan_time}}
            )
            return jsonify({"msg": "Exit successful. Have a safe trip!"}), 200

        # ---------------------------------------------------------
        # 🏠 CASE 2: ENTRY SCAN (Student is returning to campus)
        # ---------------------------------------------------------
        if not outpass.get("scannedEntry"):
            # Logic: We DO NOT block entry even if scan_time > to_time.
            # We just record if they were late.
            is_late = scan_time > to_time
            
            update_fields = {
                "scannedEntry": True,
                "entryTime": scan_time,
                "lateReturn": is_late
            }

            requests_collection.update_one(
                {"_id": ObjectId(request_id)},
                {"$set": update_fields}
            )

            if is_late:
                return jsonify({"msg": "Entry recorded. Warning: You returned LATE."}), 200
            return jsonify({"msg": "Welcome back! Entry successful."}), 200

        return jsonify({"msg": "Outpass already completed."}), 400

    except Exception as e:
        return jsonify({"msg": "Error", "error": str(e)}), 500

# ----------------------------
# Security: Get Students Currently Out
# ----------------------------
# ----------------------------
# Security & Warden: Get Students Currently Out
# ----------------------------
@outpass_bp.route("/security/active", methods=["GET"])
@jwt_required()
def get_security_active_outpasses():
    try:
        user_id = get_jwt_identity()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        # FIX: Allow both 'security' AND 'warden' to access this list
        if not user or user.get("role") not in ["security", "warden"]:
            return jsonify({"msg": "Unauthorized: Access restricted to staff"}), 403

        active_outpasses = list(requests_collection.find({
            "status": "approved",
            "scannedExit": True,
            "scannedEntry": False
        }))

        for op in active_outpasses:
            student = users_collection.find_one({"_id": ObjectId(op["studentId"])}, {"username": 1, "email": 1})
            op["studentName"] = student.get("username", "Unknown") if student else "Unknown"
            op["studentEmail"] = student.get("email", "Unknown") if student else "Unknown"
            format_outpass(op)

        return jsonify({"active_outpasses": active_outpasses}), 200
    except Exception as e:
        return jsonify({"msg": "Error fetching active outpasses", "error": str(e)}), 500