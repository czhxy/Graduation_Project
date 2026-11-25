# code/scripts/00_check_env.py
# 用法：python scripts/00_check_env.py              只查环境（第 1 周）
#       python scripts/00_check_env.py --with-clip  加 open_clip 加载与吞吐（第 3 周）
import argparse, platform, time
import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-clip", action="store_true")
    ap.add_argument("--batch", type=int, default=8)
    args = ap.parse_args()
    gb = lambda n: f"{n / 1024 ** 3:.2f} GB"

    print("1) Python :", platform.python_version(), "|", platform.platform())
    print("2) PyTorch:", torch.__version__, "| 编译 CUDA:", torch.version.cuda)
    ok = torch.cuda.is_available()
    print("3) CUDA 可用:", ok)
    if not ok:
        print("   [失败] 多半装成了 CPU 版 torch 或驱动异常")
        return
    dev = torch.device("cuda:0")
    p = torch.cuda.get_device_properties(0)
    print("4) GPU:", p.name, "| 显存", gb(p.total_memory),
          f"({p.total_memory / 1024 ** 2:.0f} MiB) | sm_{p.major}{p.minor}")

    a, b = torch.randn(1024, 1024, device=dev), torch.randn(1024, 1024, device=dev)
    torch.cuda.synchronize()
    c = a @ b
    torch.cuda.synchronize()
    print("5) 随机张量前向(1024x1024 matmul): OK | 均值 %.4f" % c.mean().item())

    x, w = torch.randn(4096, 768, device=dev), torch.randn(768, 768, device=dev)
    for _ in range(5):
        x @ w
    torch.cuda.synchronize()
    t0, n = time.time(), 20
    for _ in range(n):
        x @ w
    torch.cuda.synchronize()
    print(f"6) 稠密矩阵乘吞吐: {2 * 4096 * 768 * 768 * n / (time.time() - t0) / 1e12:.1f} TFLOPS")

    if args.with_clip:
        import open_clip
        print("7) open_clip 加载测试（首次会下载约 0.6 GB 权重）")
        model, _, _ = open_clip.create_model_and_transforms("ViT-B-16", pretrained="openai")
        model = model.to(dev).eval()
        for q in model.parameters():
            q.requires_grad_(False)          # 冻结：本课题不做任何训练
        tok = open_clip.get_tokenizer("ViT-B-16")
        xb = torch.randn(args.batch, 3, 224, 224, device=dev)
        with torch.no_grad():
            txt = model.encode_text(tok(["a photo of a waterbird.",
                                         "a photo of a landbird."]).to(dev))
            txt = txt / txt.norm(dim=-1, keepdim=True)
            fe = model.encode_image(xb)
            fe = fe / fe.norm(dim=-1, keepdim=True)
            for _ in range(3):
                model.encode_image(xb)
            torch.cuda.synchronize()
            t0, n = time.time(), 10
            for _ in range(n):
                model.encode_image(xb)
            torch.cuda.synchronize()
        print("   特征形状:", tuple(fe.shape), "| 相似度(随机图):", (fe @ txt.T * 100).tolist())
        print(f"   真实吞吐: {args.batch * n / (time.time() - t0):.1f} img/s"
              f" | 峰值显存 {gb(torch.cuda.max_memory_allocated(0))}")
        print("   [OK] 冻结 + 前向 + 文本相似度 全链路可用")

    print("SELF-CHECK PASS")


if __name__ == "__main__":
    main()
