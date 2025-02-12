import sys
import asyncio
import math
import logging
from typing import List, Dict

sys.path.append("/Users/jonathanlaw/Documents/docs/data_ver")

# Initialize API key into the environment securely
import packages
from packages.common import pd, os, requests, load_bar
from packages.bland_AI import *

# Remove invalid syntax
# åç

# Configure logging
logging.basicConfig(
    filename='bland_async.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

bland_api_key = os.environ.get("BLAND_API_KEY")
if not bland_api_key:
    raise ValueError("BLAND_API_KEY environment variable not set.")

questions = [
    ["was the identity confirmed", "boolean"], 
    ["was the company confirmed", "boolean"],
    ["was the expected name in voicemail", "boolean"],
    ["was the expected company name in voicemail", "boolean"],
    ["who picked up human or voicemail", "string"], 
]

# Extract only question texts
question_texts = [q[0] for q in questions]

payload = {
    "goal": "determine if the person confirmed their identity and the company they're with",
    "questions": questions
}

header_variables = ["phone_number", "Name", "Business", "City"]
additional_columns = ["answered_by", "recording_url", "call_status", "queue_status", "error_message"]
df_columns = header_variables + additional_columns + question_texts

batch_size = 50
batch_ids = [
    "08beec92-d23b-4f2a-bed8-a78e7658bada",
]
export_direc = "/Users/jonathanlaw/Documents/docs/data_ver/data_ver_results"
export_fn = "20240915_test.csv"

rows = []

for batch_id in batch_ids:
    status = "error"

    if status == "error":
        print(f"Proceeding w/ call-by-call analysis for batch: {batch_id}...")
        logging.info(f"Starting analysis for batch_id: {batch_id}")
        
        response_gbd = get_batch_details(batch_id=batch_id).json()
        call_ids = response_gbd.get("analysis", {}).get("call_ids", [])
        
        if not call_ids:
            logging.warning(f"No call IDs found for batch_id: {batch_id}")
            continue
        
        call_id_batches = math.ceil(len(call_ids) / batch_size)
        logging.info(f"Total call_ids: {len(call_ids)}, Batches: {call_id_batches}")
        
        for idx_cib in range(call_id_batches):
            batch_processing = call_ids[idx_cib * batch_size : (idx_cib + 1) * batch_size]
            logging.info(f"Processing batch {idx_cib + 1}/{call_id_batches} with {len(batch_processing)} call_ids")
            
            try:
                processed_rows = asyncio.run(process_all_calls(call_ids=batch_processing, payload=payload, header_variables=header_variables))
                
                for row in processed_rows:
                    if len(row) != len(df_columns):
                        logging.error(f"Row length mismatch: expected {len(df_columns)}, got {len(row)}. Row: {row}")
                        # Handle as needed: skip, pad, etc.
                        continue
                    rows.append(row)
            except Exception as e:
                logging.error(f"Error processing batch {idx_cib + 1}: {e}")
                continue
        
        # Create DataFrame and export
        if rows:
            df_initial = pd.DataFrame(rows, columns=df_columns)
            df_initial.to_csv(os.path.join(export_direc, export_fn), index=False)
            logging.info(f"Exported data to {os.path.join(export_direc, export_fn)}")
        else:
            logging.warning("No rows to export.")
    
    else:
        quit(f"Status is {status}!")