import json
import subprocess

REPOS = ["syedashfaq/CUB_200_2011", "student/CUB_birds_200_2011",
         "weiywang/CUB_200_2011_CAP", "bentrevett/caltech-ucsd-birds-200-2011",
         "dpdl-benchmark/caltech_birds2011"]

for repo in REPOS:
    url = f"https://huggingface.co/api/datasets/{repo}/tree/main?recursive=true"
    out = subprocess.run(["curl.exe", "-sS", "--max-time", "40", url],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        items = json.loads(out.stdout.lstrip("\ufeff"))
    except Exception as e:
        print(f"{repo}: parse fail {e}")
        continue
    files = [x["path"] for x in items if x.get("type") == "file"]
    seg = [f for f in files if "segmentation" in f.lower()]
    total = sum(x.get("size", 0) or 0 for x in items if x.get("type") == "file")
    print(f"{repo}: files={len(files)} seg_files={len(seg)} size={total/1e9:.2f}GB")
    if seg:
        print("   seg 示例:", seg[:2])
    for f in files[:5]:
        print("   ·", f)
