import os
import random
import argparse
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

STAFF_TYPES = ["Permanent Staff", "Visiting Consultant", "Intern", "Outsourced Technician"]
ROLES = ["Doctor", "Nurse", "Consultant", "Intern", "Lab Technician", "Radiology Technician", "Pharmacist", "Billing Staff"]
DEPARTMENTS = ["ICU", "Emergency", "Pharmacy", "Radiology", "Laboratory", "Billing", "HR", "Administration"]
APPLICATIONS = ["Patient Records", "Pharmacy", "Laboratory", "Radiology", "Billing", "HR", "Administration"]
PERMISSIONS = ["READ", "WRITE", "READ_WRITE", "ADMIN"]
ACTIONS = ["LOGIN", "VIEW_RECORD", "EDIT_RECORD", "DISPENSE_MED", "RUN_TEST", "EXPORT_REPORT", "DELETE_LOG"]

FIRST_NAMES = ["Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Neha", "Arjun", "Kavya", "Sanjay", "Meera",
               "Rahul", "Pooja", "Amit", "Sneha", "Karan", "Ritu", "Deepak", "Swati", "Nikhil", "Divya",
               "John", "Sarah", "David", "Emily", "Michael", "Jessica", "James", "Amanda", "Robert", "Stephanie"]

LAST_NAMES = ["Sharma", "Verma", "Patel", "Rao", "Gupta", "Nair", "Reddy", "Singh", "Kumar", "Joshi",
              "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

def generate_synthetic_data(num_users=200, num_events=5200, num_decisions=100, seed=42):
    """
    Generates synthetic hospital dataset reproducibly using a fixed random seed.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    random.seed(seed)

    # 1. Generate Users (users.csv)
    users = []
    managers = ["Dr. Rajesh Sharma", "Dr. Anita Desai", "Dr. Suresh Menon", "Manager Sunita Rao", "Dr. Paul Walker"]
    start_date = datetime.now() - timedelta(days=365*3)

    for i in range(1, num_users + 1):
        user_id = f"USR-{1000 + i}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        role = random.choice(ROLES)
        
        if role == "Consultant":
            staff_type = "Visiting Consultant"
        elif role == "Intern":
            staff_type = "Intern"
        else:
            staff_type = random.choice(["Permanent Staff", "Outsourced Technician"])
            
        department = random.choice(DEPARTMENTS)
        manager = random.choice(managers)
        # ~15% inactive users
        status = "ACTIVE" if random.random() > 0.15 else "INACTIVE"
        join_days = random.randint(10, 1000)
        join_date = (start_date + timedelta(days=join_days)).strftime("%Y-%m-%d")

        users.append({
            "user_id": user_id,
            "name": name,
            "department": department,
            "role": role,
            "staff_type": staff_type,
            "manager": manager,
            "status": status,
            "join_date": join_date
        })

    df_users = pd.DataFrame(users)
    users_csv_path = os.path.join(DATA_DIR, "users.csv")
    df_users.to_csv(users_csv_path, index=False)

    # 2. Generate Entitlements (entitlements.csv: 500 - 1000 entitlements)
    entitlements = []
    ent_id_counter = 5000

    for i, user in df_users.iterrows():
        user_id = user["user_id"]
        role = user["role"]
        
        # Grant 2 to 5 entitlements per user -> total ~700 entitlements
        num_user_ents = random.randint(2, 5)
        
        # Determine subset of applications for entitlement assignment
        user_apps = random.sample(APPLICATIONS, k=min(num_user_ents, len(APPLICATIONS)))
        
        for app in user_apps:
            ent_id_counter += 1
            
            # High permission ADMIN assigned to some entitlements (~12%)
            p_rand = random.random()
            if p_rand < 0.12:
                permission = "ADMIN"
            elif p_rand < 0.35:
                permission = "READ_WRITE"
            elif p_rand < 0.65:
                permission = "WRITE"
            else:
                permission = "READ"
                
            granted_days = random.randint(5, 300)
            granted_date = (datetime.now() - timedelta(days=granted_days)).strftime("%Y-%m-%d")
            status = "ACTIVE" if random.random() > 0.1 else "REVOKED"

            entitlements.append({
                "entitlement_id": f"ENT-{ent_id_counter}",
                "user_id": user_id,
                "application": app,
                "permission": permission,
                "granted_date": granted_date,
                "status": status
            })

    df_entitlements = pd.DataFrame(entitlements)
    entitlements_csv_path = os.path.join(DATA_DIR, "entitlements.csv")
    df_entitlements.to_csv(entitlements_csv_path, index=False)

    # 3. Generate Usage Events (usage_events.csv: 5000+ events)
    usage_events = []
    now = datetime.now()
    
    # Active entitlements map
    active_ents = df_entitlements[df_entitlements["status"] == "ACTIVE"]

    # Assign usage distributions so some entitlements are completely unused or heavily used
    # Leave 20% of active entitlements completely UNUSED
    active_ent_list = active_ents.to_dict("records")
    used_ents = random.sample(active_ent_list, k=int(len(active_ent_list) * 0.8))

    for i in range(1, num_events + 1):
        event_id = f"EVT-{100000 + i}"
        
        # Select random entitlement from used entitlements
        ent = random.choice(used_ents)
        user_id = ent["user_id"]
        app = ent["application"]
        action = random.choice(ACTIONS)
        
        # Event timestamp (within past 90 days)
        event_offset_minutes = random.randint(0, 90 * 24 * 60)
        event_ts = now - timedelta(minutes=event_offset_minutes)
        
        # Received timestamp (normal vs delayed)
        if random.random() < 0.05: # 5% delayed events
            delay_minutes = random.randint(120, 4320) # 2h to 3 days delayed
            received_ts = event_ts + timedelta(minutes=delay_minutes)
        else:
            received_ts = event_ts + timedelta(seconds=random.randint(1, 30))

        usage_events.append({
            "event_id": event_id,
            "user_id": user_id,
            "application": app,
            "action": action,
            "event_timestamp": event_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "received_timestamp": received_ts.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Add 150 Duplicate Events (TEST 1 scenario)
    for _ in range(150):
        dup_event = random.choice(usage_events).copy()
        dup_ts = datetime.strptime(dup_event["received_timestamp"], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=10)
        dup_event["received_timestamp"] = dup_ts.strftime("%Y-%m-%d %H:%M:%S")
        usage_events.append(dup_event)

    # Add 50 Invalid / Missing value Events (TEST 4 scenario)
    for i in range(50):
        invalid_evt = {
            "event_id": f"EVT-INV-{i+1}",
            "user_id": None if i % 2 == 0 else "USR-INVALID-9999",
            "application": "UnknownApp" if i % 3 == 0 else "Patient Records",
            "action": "INVALID_ACTION",
            "event_timestamp": "INVALID_DATE" if i % 4 == 0 else now.strftime("%Y-%m-%d %H:%M:%S"),
            "received_timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        usage_events.append(invalid_evt)

    # Shuffle events to create out-of-order sequence (TEST 3 scenario)
    random.shuffle(usage_events)

    df_usage = pd.DataFrame(usage_events)
    usage_csv_path = os.path.join(DATA_DIR, "usage_events.csv")
    df_usage.to_csv(usage_csv_path, index=False)

    # 4. Generate Initial Review Decisions
    review_decisions = []
    reviewers = ["Reviewer Alice (Security Lead)", "Reviewer Bob (Compliance Officer)", "Reviewer Carol (Access Admin)"]
    
    sample_ents = df_entitlements.sample(n=min(num_decisions, len(df_entitlements))).copy()
    
    for i, (_, ent) in enumerate(sample_ents.iterrows()):
        decision_id = f"DEC-{2000 + i + 1}"
        u_id = ent["user_id"]
        e_id = ent["entitlement_id"]
        
        risk_score = random.randint(10, 85)
        if risk_score >= 60:
            recommendation = "REVOKE"
        elif risk_score >= 30:
            recommendation = "REVIEW"
        else:
            recommendation = "APPROVE"

        if random.random() < 0.65:
            reviewer_decision = "APPROVE"
            override = True if recommendation != "APPROVE" else False
            reason = "Standard baseline approval" if not override else "Legacy manager verbal confirmation"
        else:
            reviewer_decision = recommendation
            override = False
            reason = "Aligned with system recommendation"

        decision_ts = (now - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d %H:%M:%S")

        review_decisions.append({
            "decision_id": decision_id,
            "user_id": u_id,
            "entitlement_id": e_id,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "reviewer_decision": reviewer_decision,
            "override": override,
            "reason": reason,
            "reviewer": random.choice(reviewers),
            "decision_timestamp": decision_ts
        })

    df_decisions = pd.DataFrame(review_decisions)
    decisions_csv_path = os.path.join(DATA_DIR, "review_decisions.csv")
    df_decisions.to_csv(decisions_csv_path, index=False)

    print(f"[OK] Generated Synthetic Dataset successfully (Seed={seed}):")
    print(f"  -> {users_csv_path} ({len(df_users)} records)")
    print(f"  -> {entitlements_csv_path} ({len(df_entitlements)} records)")
    print(f"  -> {usage_csv_path} ({len(df_usage)} records)")
    print(f"  -> {decisions_csv_path} ({len(df_decisions)} records)")
    
    return {
        "users": len(df_users),
        "entitlements": len(df_entitlements),
        "events": len(df_usage),
        "decisions": len(df_decisions)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic hospital access review dataset.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--users", type=int, default=200, help="Number of synthetic users (default: 200)")
    parser.add_argument("--events", type=int, default=5200, help="Number of usage events (default: 5200)")
    args = parser.parse_args()

    generate_synthetic_data(num_users=args.users, num_events=args.events, seed=args.seed)
