#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import csv
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_INPUT_FILE = os.path.join(BASE_DIR, 'data', 'raw', 'raw_selections.json')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Spelling corrections & name normalization mapping
NAME_CORRECTIONS = {
    "邝兆雷": "邝兆镭",
    "廖梓成傲": "廖梓成",
    "万向": "万项",
    "汪修号": "汪修昊"
}

# Positions standardization
POSITION_STANDARDIZATION = {
    "锋线": "前锋",
    "锋线尖刀": "前锋",
    "边锋": "前锋",
    "右边锋": "前锋",
    "左后卫": "后卫",
    "右边后卫": "后卫",
    "后腰": "中场",
    "前腰": "中场"
}

def normalize_name(name: str) -> str:
    cleaned = name.strip()
    return NAME_CORRECTIONS.get(cleaned, cleaned)

def normalize_position(pos: str) -> str:
    cleaned = pos.strip() if pos else "未知"
    return POSITION_STANDARDIZATION.get(cleaned, cleaned)

def main():
    if not os.path.exists(RAW_INPUT_FILE):
        print(f"Error: Raw file {RAW_INPUT_FILE} not found. Run scrape_sources.py first.")
        return

    with open(RAW_INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_records = json.load(f)

    clean_records = []

    for r in raw_records:
        player_name = normalize_name(r["player_name"])
        pos = normalize_position(r["position"])
        
        # Check source presence to categorize status
        has_relation_src = bool(r["relation_source_url"])
        has_national_src = bool(r["national_team_source_url"])
        
        # Determine selection type and national team level
        is_selected = bool(r["national_team_level"] and r["national_team_source_url"])
        
        # Determine confirmation status
        if has_relation_src and has_national_src and is_selected:
            status = "confirmed"
        elif (has_relation_src or has_national_src) and is_selected:
            status = "partially_confirmed"
        else:
            status = "pending"

        # Determine confidence level
        confidence = "high"
        if status == "partially_confirmed":
            confidence = "medium"
        elif status == "pending":
            confidence = "low"

        # Update fields
        r["player_name"] = player_name
        r["position"] = pos
        r["confidence"] = confidence
        
        # Store verification status in notes or new field if needed
        # We can append it to the notes for readability, or keep it in player notes
        notes_list = []
        if r.get("notes"):
            notes_list.append(r["notes"])
        notes_list.append(f"验证状态: {status}")
        r["notes"] = "; ".join(notes_list)
        
        clean_records.append(r)

    # Save to processed json
    processed_json_file = os.path.join(PROCESSED_DIR, 'players_clean.json')
    with open(processed_json_file, 'w', encoding='utf-8') as f:
        json.dump(clean_records, f, ensure_ascii=False, indent=4)
    print(f"Saved {len(clean_records)} normalized records to {processed_json_file}")

    # Save to outputs players_national_team_selection.csv
    csv_file = os.path.join(OUTPUTS_DIR, 'players_national_team_selection.csv')
    fields = [
        "player_name", "birth_year", "age_group", "position", "current_or_listed_club",
        "football_xiaojiang_relation", "relation_source_url", "national_team_level",
        "team_name_official", "selection_type", "selection_date", "event_or_context",
        "source_priority", "national_team_source_url", "source_title", "confidence", "notes"
    ]
    
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in clean_records:
            # age_group represents the Football Xiaojiang age group (often same as birth_year)
            # if birth_year is missing, we write empty.
            row = {
                "player_name": r["player_name"],
                "birth_year": r["birth_year"] if r["birth_year"] else "",
                "age_group": r["birth_year"] if r["birth_year"] else "", # matching birth year as default
                "position": r["position"],
                "current_or_listed_club": r["current_or_listed_club"],
                "football_xiaojiang_relation": r["football_xiaojiang_relation"],
                "relation_source_url": r["relation_source_url"],
                "national_team_level": r["national_team_level"],
                "team_name_official": r["team_name_official"],
                "selection_type": r["selection_type"],
                "selection_date": r["selection_date"],
                "event_or_context": r["event_or_context"],
                "source_priority": r["source_priority"],
                "national_team_source_url": r["national_team_source_url"],
                "source_title": r["source_title"],
                "confidence": r["confidence"],
                "notes": r["notes"]
            }
            writer.writerow(row)
            
    print(f"Saved selections CSV to {csv_file}")

if __name__ == "__main__":
    main()
