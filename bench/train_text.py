"""P0c step 2 (quick): fine-tune bert-mini-arabic on OSACT 2020 (offensive or not) and compare with our word list.
Data: datasets/osact2020/{train,dev}.txt from the OSACT4 shared task (test labels are not public, so dev is our test set).
Run from bench/: ../.venv/bin/python train_text.py   (CPU, a few minutes)"""
import random, sys, time
from pathlib import Path
import numpy as np, torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

sys.path.insert(0, "../wordlists"); from build_ar import normalize  # same cleaning as the list builder

REPO, SEQ, EPOCHS, BS, LR = "asafaya/bert-mini-arabic", 64, 4, 32, 5e-5
random.seed(0); torch.manual_seed(0)

def load(name):
    rows = [l.rstrip("\n").split("\t") for l in open(f"datasets/osact2020/{name}.txt", encoding="utf-8") if "\t" in l]
    return [r[0].replace("<LF>", " ") for r in rows], [int(r[1] == "OFF") for r in rows]

def f1s(y, p):  # macro-F1 (the OSACT metric) and F1 of the offensive class
    out = []
    for c in (0, 1):
        tp = sum(a == c and b == c for a, b in zip(y, p)); fp = sum(a != c and b == c for a, b in zip(y, p)); fn = sum(a == c and b != c for a, b in zip(y, p))
        out.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return sum(out) / 2, out[1]

xtr, ytr = load("train"); xte, yte = load("dev")
assert len(xtr) == 7000 and len(xte) == 1000, (len(xtr), len(xte))

# Baseline: our word list (Arabic single words only), whole-word match after normalization
import csv
words = {r["key"] for r in csv.DictReader(open("../wordlists/ar_combined.tsv", encoding="utf-8"), delimiter="\t")
         if r["script"] == "arabic" and r["words"] == "1"}
plist = [int(any(w in words for w in normalize(x).split())) for x in xte]
print(f"word list ({len(words)} words): macro-F1 {f1s(yte, plist)[0]:.3f}, offensive-F1 {f1s(yte, plist)[1]:.3f}", flush=True)

tok = AutoTokenizer.from_pretrained(REPO)
model = AutoModelForSequenceClassification.from_pretrained(REPO, num_labels=2)
enc = lambda xs: tok(xs, truncation=True, max_length=SEQ, padding="max_length", return_tensors="pt")
Xtr, Xte = enc(xtr), enc(xte); Ytr = torch.tensor(ytr)
# ponytail: plain class weights for the 80/20 imbalance, no sampler or tuning
loss_fn = torch.nn.CrossEntropyLoss(weight=torch.tensor([1.0, 5590 / 1410]))
opt = torch.optim.AdamW(model.parameters(), lr=LR)

def predict():
    model.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(xte), 128):
            out += model(input_ids=Xte["input_ids"][i:i + 128], attention_mask=Xte["attention_mask"][i:i + 128]).logits.argmax(-1).tolist()
    return out

t0 = time.time()
for ep in range(EPOCHS):
    model.train(); idx = list(range(len(xtr))); random.shuffle(idx)
    for i in range(0, len(idx), BS):
        b = idx[i:i + BS]
        loss = loss_fn(model(input_ids=Xtr["input_ids"][b], attention_mask=Xtr["attention_mask"][b]).logits, Ytr[b])
        opt.zero_grad(); loss.backward(); opt.step()
    p = predict(); m, o = f1s(yte, p)
    print(f"epoch {ep + 1}: macro-F1 {m:.3f}, offensive-F1 {o:.3f} ({time.time() - t0:.0f} s)", flush=True)

both = [max(a, b) for a, b in zip(p, plist)]
print(f"model OR list: macro-F1 {f1s(yte, both)[0]:.3f}, offensive-F1 {f1s(yte, both)[1]:.3f}")
