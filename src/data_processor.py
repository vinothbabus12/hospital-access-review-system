import os
import pandas as pd
import numpy as np
from datetime import datetime


class DataProcessor:
    def __init__(self, df_users=None, df_entitlements=None, df_events=None):
        """
        Initializes DataProcessor with users, entitlements, and usage events dataframes or file paths.
        Raw input data structures remain unchanged.
        """
        self.raw_users = self._to_dataframe(df_users)
        self.raw_entitlements = self._to_dataframe(df_entitlements)
        self.raw_events = self._to_dataframe(df_events)

        self.clean_events = pd.DataFrame()
        self.invalid_events = pd.DataFrame()
        self.quality_summary = {
            "total_events": 0,
            "duplicate_events": 0,
            "invalid_events": 0,
            "delayed_events": 0,
            "out_of_order_events": 0,
            "valid_events": 0
        }

        self.process_events()

    def _to_dataframe(self, data):
        """
        Converts input string path, DataFrame, list of dicts, or None into a clean DataFrame copy.
        """
        if data is None:
            return pd.DataFrame()
        if isinstance(data, str):
            if os.path.exists(data):
                return pd.read_csv(data)
            return pd.DataFrame()
        if isinstance(data, pd.DataFrame):
            return data.copy()
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame()

    def process_events(self):
        """
        Processes usage events by:
        1. Validating required fields and timestamps without crashing on corrupt rows.
        2. Detecting and flagging invalid events.
        3. Detecting and removing duplicate event_ids to prevent double counting.
        4. Identifying delayed events (received_timestamp > event_timestamp by > 1 hr).
        5. Identifying out-of-order events.
        6. Sorting clean valid events chronologically by event_timestamp.
        7. Returning a comprehensive data quality report.
        """
        if self.raw_events.empty:
            self.quality_summary = {
                "total_events": 0,
                "duplicate_events": 0,
                "invalid_events": 0,
                "delayed_events": 0,
                "out_of_order_events": 0,
                "valid_events": 0
            }
            return self.quality_summary

        total_raw = len(self.raw_events)

        def is_valid_record(row):
            try:
                # 1. Validate user_id (not NaN, None, or empty)
                user_id = row.get("user_id")
                if pd.isna(user_id) or user_id is None or str(user_id).strip() == "" or str(user_id).strip().lower() == "none" or str(user_id).strip().lower() == "nan":
                    return False

                # 2. Validate application and action
                app = row.get("application")
                action = row.get("action")
                if pd.isna(app) or str(app).strip() == "":
                    return False
                if pd.isna(action) or str(action).strip() == "":
                    return False

                # 3. Validate timestamps presence and parseability
                evt_ts = row.get("event_timestamp")
                rec_ts = row.get("received_timestamp")
                if pd.isna(evt_ts) or pd.isna(rec_ts):
                    return False

                pd.to_datetime(evt_ts)
                pd.to_datetime(rec_ts)
                return True
            except Exception:
                return False

        valid_mask = self.raw_events.apply(is_valid_record, axis=1)

        self.invalid_events = self.raw_events[~valid_mask].copy()
        valid_records = self.raw_events[valid_mask].copy()
        num_invalid = len(self.invalid_events)

        if valid_records.empty:
            self.clean_events = pd.DataFrame()
            self.quality_summary = {
                "total_events": total_raw,
                "duplicate_events": 0,
                "invalid_events": num_invalid,
                "delayed_events": 0,
                "out_of_order_events": 0,
                "valid_events": 0
            }
            return self.quality_summary

        # Deduplication based on event_id (or identical event attributes)
        dedup_records = valid_records.drop_duplicates(subset=["event_id"], keep="first").copy()
        if "user_id" in dedup_records.columns and "application" in dedup_records.columns and "action" in dedup_records.columns and "event_timestamp" in dedup_records.columns:
            dedup_records = dedup_records.drop_duplicates(subset=["user_id", "application", "action", "event_timestamp"], keep="first")

        num_duplicates = len(valid_records) - len(dedup_records)

        # Handle delayed events & timestamp conversion
        dedup_records["event_dt"] = pd.to_datetime(dedup_records["event_timestamp"])
        dedup_records["received_dt"] = pd.to_datetime(dedup_records["received_timestamp"])

        # Delayed event check (> 3600 seconds delay between event time and received time)
        dedup_records["is_delayed"] = (dedup_records["received_dt"] - dedup_records["event_dt"]).dt.total_seconds() > 3600
        num_delayed = int(dedup_records["is_delayed"].sum())

        # Out-of-order detection (arrival sequence vs event timestamp sequence)
        rec_sorted = dedup_records.sort_values(by="received_dt").reset_index(drop=True)
        evt_sorted = dedup_records.sort_values(by="event_dt").reset_index(drop=True)

        if "event_id" in rec_sorted.columns:
            out_of_order_count = int((rec_sorted["event_id"] != evt_sorted["event_id"]).sum())
        else:
            out_of_order_count = 0

        # Clean events sorted chronologically by event_timestamp
        self.clean_events = evt_sorted.copy()
        num_valid = len(self.clean_events)

        self.quality_summary = {
            "total_events": total_raw,
            "duplicate_events": num_duplicates,
            "invalid_events": num_invalid,
            "delayed_events": num_delayed,
            "out_of_order_events": out_of_order_count,
            "valid_events": num_valid
        }
        return self.quality_summary

    def get_quality_report(self):
        """
        Returns the data quality report containing event counts and flags.
        """
        return self.quality_summary

    def get_peer_usage_baseline(self):
        """
        Calculates usage counts per user per application from clean_events,
        computes last usage date, and computes peer average & median usage for users
        with the same role and application.
        Preserves correct statistics despite delayed/out-of-order events.
        """
        if self.raw_users.empty or self.raw_entitlements.empty:
            return pd.DataFrame()

        # Merge entitlements with user roles and staff types
        # Rename entitlement 'status' before merge to avoid status_x / status_y
        # ambiguity that would break INACTIVE_USER detection in the evidence engine.
        ent_cols = self.raw_entitlements.copy()
        ent_cols = ent_cols.rename(columns={"status": "entitlement_status"})

        ent_users = pd.merge(
            ent_cols,
            self.raw_users[["user_id", "name", "role", "staff_type", "department", "status"]],
            on="user_id",
            how="inner"
        )

        # Count events per user per application and record last usage date
        if not self.clean_events.empty:
            event_stats = self.clean_events.groupby(["user_id", "application"]).agg(
                user_usage=("event_id", "count"),
                last_usage_date=("event_timestamp", "max")
            ).reset_index()
        else:
            event_stats = pd.DataFrame(columns=["user_id", "application", "user_usage", "last_usage_date"])

        # Merge usage count into entitlement-user table
        merged = pd.merge(ent_users, event_stats, on=["user_id", "application"], how="left")
        merged["user_usage"] = merged["user_usage"].fillna(0).astype(int)
        merged["last_usage_date"] = merged["last_usage_date"].fillna("Never")

        # Calculate Peer Role Statistics per (role, application)
        # Peers are users with the same role for the given application
        peer_stats = merged.groupby(["role", "application"])["user_usage"].agg(
            peer_average="mean",
            peer_median="median",
            peer_count="count"
        ).reset_index()

        peer_stats["peer_average"] = peer_stats["peer_average"].round(1)
        peer_stats["peer_median"] = peer_stats["peer_median"].round(1)

        # Merge peer stats back
        result = pd.merge(merged, peer_stats, on=["role", "application"], how="left")
        result["peer_average"] = result["peer_average"].fillna(0.0)
        result["peer_median"] = result["peer_median"].fillna(0.0)
        result["usage_difference"] = (result["user_usage"] - result["peer_average"]).round(1)
        result["difference_from_peer"] = result["usage_difference"]

        return result

