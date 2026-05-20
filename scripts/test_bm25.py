"""Test fastembed BM25 with onnxruntime stubbed out."""
import sys, types

# Stub onnxruntime before anything imports it
ort_mock = types.ModuleType("onnxruntime")
ort_mock.SessionOptions = type("SessionOptions", (), {})
ort_mock.InferenceSession = type("InferenceSession", (), {})
ort_mock.GraphOptimizationLevel = type("GraphOptimizationLevel", (), {"ORT_ENABLE_ALL": 99})

class FakeCapiState:
    pass
ort_capi = types.ModuleType("onnxruntime.capi")
ort_capi_state = types.ModuleType("onnxruntime.capi._pybind_state")
ort_capi_state.OrtDevice = type("OrtDevice", (), {})

sys.modules["onnxruntime"] = ort_mock
sys.modules["onnxruntime.capi"] = ort_capi
sys.modules["onnxruntime.capi._pybind_state"] = ort_capi_state

sys.path.insert(0, "D:\\pip_packages")

try:
    from fastembed.sparse.bm25 import Bm25
    print("✅ BM25 imported successfully!")
    
    m = Bm25(model_name="Qdrant/bm25", cache_dir="D:\\hf_cache")
    
    # Test with blocked claims
    tests = [
        "Do not freeze VYVGART HYTRULO",
        "Discard any unused portion",
        "Wash hands with soap and water before injecting",
        "Do not attempt to warm the prefilled syringe",
        "Check the expiration date",
    ]
    
    for text in tests:
        v = list(m.embed([text]))[0]
        print(f"\n'{text}'")
        print(f"  Sparse vector: {len(v.indices)} non-zero terms")
        print(f"  Indices: {v.indices.tolist()[:8]}...")
        print(f"  Values:  {[round(x,3) for x in v.values.tolist()[:8]]}...")
        
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
