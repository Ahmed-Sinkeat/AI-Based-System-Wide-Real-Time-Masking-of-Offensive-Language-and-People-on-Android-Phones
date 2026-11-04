"""P0c step 1 (quick): export small text encoders to LiteRT for a phone speed/RAM test with bench_phone.py.
Each model: input_ids [1, 64] -> encoder -> first token -> linear head (5 categories), random head (no training: speed only).
Vocabulary cut to the first 30 000 rows to stand in for an Arabic-only trim (real trim = keep tokens seen in Arabic text).
Run from bench/: ../.venv/bin/python export_text.py"""
import shutil, subprocess, glob
from pathlib import Path
import torch
from transformers import AutoModel

SEQ, VOCAB = 64, 30_000  # ponytail: 64 tokens only (worst case per message piece); add 16/32 if 64 is borderline
MODELS = {"bertmini_ar": "asafaya/bert-mini-arabic", "bertmedium_ar": "asafaya/bert-medium-arabic",
          "e5small": "intfloat/multilingual-e5-small", "mmbertsmall": "jhu-clsp/mmBERT-small"}
OUT = Path("models_tflite"); OUT.mkdir(exist_ok=True)

class Head(torch.nn.Module):
    def __init__(self, enc):
        super().__init__(); self.enc = enc; self.fc = torch.nn.Linear(enc.config.hidden_size, 5)
    def forward(self, ids):
        return self.fc(self.enc(input_ids=ids).last_hidden_state[:, 0])

for name, repo in MODELS.items():
    want = {"fp32": "*_float32.tflite", "fp16": "*_float16.tflite", "drq": "*_dynamic_range_quant.tflite"}
    if all((OUT / f"text_{name}_{k}.tflite").exists() for k in want):
        continue
    enc = AutoModel.from_pretrained(repo, attn_implementation="eager").eval()
    emb = enc.get_input_embeddings()
    if emb.num_embeddings > VOCAB:  # trim: keep the first VOCAB rows
        new = torch.nn.Embedding(VOCAB, emb.embedding_dim); new.weight.data = emb.weight.data[:VOCAB].clone()
        enc.set_input_embeddings(new)
    params = sum(p.numel() for p in enc.parameters()) / 1e6
    work = Path(f"tflite_work/text_{name}"); shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    onnx = work / f"{name}.onnx"
    torch.onnx.export(Head(enc).eval(), (torch.randint(5, 1000, (1, SEQ)),), str(onnx), input_names=["ids"],
                      output_names=["logits"], opset_version=17, dynamo=False)
    r = subprocess.run(["../.venv/bin/onnx2tf", "-i", str(onnx), "-o", str(work), "-odrqt"], capture_output=True, text=True)
    for k, pat in want.items():
        hits = glob.glob(str(work / pat))
        if not hits:
            print("FAILED", name, k, r.stdout[-600:], r.stderr[-600:], flush=True); continue
        dst = OUT / f"text_{name}_{k}.tflite"; shutil.copy(hits[0], dst)
        print("exported", dst, f"{dst.stat().st_size / 2**20:.1f} MB, {params:.1f} M params after trim", flush=True)
