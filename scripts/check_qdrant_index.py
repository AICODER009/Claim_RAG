"""Check if Qdrant collection has full-text index on 'text' field."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from qdrant_client import QdrantClient
from new_pipeline.config import load_config

cfg = load_config()
qdrant = QdrantClient(url=cfg.qdrant.url, api_key=cfg.qdrant.api_key, timeout=30)
collection = cfg.qdrant.collection_name

info = qdrant.get_collection(collection)
print(f"Collection: {collection}")
print(f"Points: {info.points_count}")
print(f"Config: {info.config}")
print()

# Check payload indexes
print("Payload indexes:")
for field_name, field_info in (info.payload_schema or {}).items():
    print(f"  {field_name}: {field_info}")
print()

# Check if text field has a full-text index
text_schema = (info.payload_schema or {}).get("text")
if text_schema:
    print(f"Text field schema: {text_schema}")
    print(f"  Data type: {text_schema.data_type}")
    params = getattr(text_schema, 'params', None)
    print(f"  Params: {params}")
    if params:
        tokenizer = getattr(params, 'tokenizer', None)
        min_token_len = getattr(params, 'min_token_len', None)
        max_token_len = getattr(params, 'max_token_len', None)
        lowercase = getattr(params, 'lowercase', None)
        print(f"  Tokenizer: {tokenizer}")
        print(f"  Min token len: {min_token_len}")
        print(f"  Max token len: {max_token_len}")
        print(f"  Lowercase: {lowercase}")
else:
    print("❌ No text field index found! Need to create one.")

# Check Qdrant version for BM25 support
print()
try:
    from qdrant_client import models
    # Try to check if Query API supports BM25
    print("Qdrant client version supports:")
    print(f"  models.Modifier: {hasattr(models, 'Modifier')}")
    print(f"  Has 'idf' modifier: ", end="")
    try:
        # Qdrant 1.10+ has Modifier.IDF for BM25
        print(models.Modifier)
    except:
        print("No")
except Exception as e:
    print(f"Error checking: {e}")
