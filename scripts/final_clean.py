import sys, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

OUT = Path(r"D:\revisto_evidence_aligned_clean\new_pipeline\parsed\chunks_final")
ctrl_count = 0
missing_fields = 0
wrong_emb = 0
required = ["sent_id","ref_id","rt_id","text","segment_type","embeddable","numeric_tokens","vector","doc_metadata"]

for jf in sorted(OUT.glob("*.chunks.json")):
    data = json.loads(jf.read_text(encoding="utf-8"))
    for c in data:
        if c.get("embeddable"):
            ctrl = len(re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", c["text"]))
            ctrl_count += ctrl
        for f in required:
            if f not in c:
                missing_fields += 1
        if c["embeddable"] != (c["segment_type"] in ("text","table")):
            wrong_emb += 1

print(f"Control chars remaining: {ctrl_count}")
print(f"Missing required fields: {missing_fields}")
print(f"Wrong embeddable flags: {wrong_emb}")

if ctrl_count == 0 and missing_fields == 0 and wrong_emb == 0:
    print("VERDICT: GO - Ready for MedCPT embedding")
else:
    print("VERDICT: HOLD - Issues remain")
