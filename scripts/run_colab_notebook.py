"""
run_colab_notebook.py
---------------------
Connects to a running Google Colab kernel via its WebSocket URL and executes
all code cells in training/colab_train_stage1.ipynb, streaming output to the
terminal in real time.

Usage
-----
1. Open https://colab.research.google.com in your browser.
2. Open the notebook: File > Open notebook > GitHub > eddy7896/loomhash >
   training/colab_train_stage1.ipynb
3. Runtime > Change runtime type > GPU (T4).
4. Connect the runtime (click Connect top-right).  Wait until it shows "RAM / Disk" bars.
5. Get the kernel connection URL:
      Tools > Command palette > type "Show connection string" -- OR --
      open the URL:  https://colab.research.google.com/tun/m/<id>/api/kernels/<kid>/channels
      (visible in the browser's Network tab when you run a cell -- filter on "channels")
6. Run this script:
      python scripts/run_colab_notebook.py --url <ws_url> [--token <token>]

   where <ws_url> is the wss:// kernel channels URL from step 5.

Alternatively just set these env vars before running:
   COLAB_KERNEL_URL   wss://... URL
   COLAB_TOKEN        (optional) the ?authuser= bearer or colab token if required
"""

import argparse
import json
import os
import sys
import time
import uuid

try:
    from jupyter_kernel_client import KernelWebSocketClient
except ImportError:
    sys.exit("jupyter_kernel_client not installed. Run: pip install jupyter-kernel-client")

NOTEBOOK_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "training", "colab_train_stage1.ipynb",
)


def load_code_cells(notebook_path: str) -> list[dict]:
    """Return a list of {index, source} dicts for every code cell in the notebook."""
    with open(notebook_path, encoding="utf-8") as f:
        nb = json.load(f)
    cells = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = cell["source"]
        if isinstance(src, list):
            src = "".join(src)
        src = src.strip()
        if src:
            cells.append({"index": i, "source": src})
    return cells


def execute_cell(client: KernelWebSocketClient, source: str, cell_num: int, total: int):
    """Send one cell to the kernel and print output as it arrives."""
    print(f"\n{'='*60}")
    print(f"[Cell {cell_num}/{total}]")
    print(f"{'='*60}")
    # Print a short preview of the cell
    preview = source[:200].replace("\n", "\\n")
    print(f"  >> {preview}{'...' if len(source) > 200 else ''}")
    print()

    try:
        result = client.execute(source)
    except Exception as exc:
        print(f"  ERROR sending cell: {exc}")
        return False

    # result is typically a list of output dicts or a single object
    outputs = result if isinstance(result, list) else [result]
    had_error = False
    for output in outputs:
        if output is None:
            continue
        # jupyter_kernel_client may return dicts or objects
        if hasattr(output, "output_type"):
            otype = output.output_type
            if otype == "stream":
                text = getattr(output, "text", "")
                print(text, end="", flush=True)
            elif otype in ("display_data", "execute_result"):
                data = getattr(output, "data", {})
                text = data.get("text/plain", "") if isinstance(data, dict) else str(data)
                print(text)
            elif otype == "error":
                ename = getattr(output, "ename", "Error")
                evalue = getattr(output, "evalue", "")
                traceback = getattr(output, "traceback", [])
                print(f"\n[ERROR] {ename}: {evalue}")
                for line in traceback:
                    # strip ANSI escape codes for cleaner terminal output
                    import re
                    clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
                    print(clean)
                had_error = True
        elif isinstance(output, dict):
            otype = output.get("output_type") or output.get("msg_type", "")
            if otype == "stream":
                print(output.get("text", ""), end="", flush=True)
            elif otype in ("display_data", "execute_result"):
                data = output.get("data", {})
                print(data.get("text/plain", str(data)))
            elif otype == "error":
                print(f"\n[ERROR] {output.get('ename','Error')}: {output.get('evalue','')}")
                for line in output.get("traceback", []):
                    import re
                    print(re.sub(r"\x1b\[[0-9;]*m", "", line))
                had_error = True
            else:
                # Unknown output type — dump it so nothing is hidden
                raw = str(output)
                if raw.strip():
                    print(f"  [output] {raw[:300]}")
        else:
            raw = str(output)
            if raw.strip():
                print(raw)

    return not had_error


def main():
    parser = argparse.ArgumentParser(description="Run the LoomHash Colab training notebook remotely.")
    parser.add_argument("--url", default=os.environ.get("COLAB_KERNEL_URL"),
                        help="wss:// kernel channels WebSocket URL from Colab")
    parser.add_argument("--token", default=os.environ.get("COLAB_TOKEN", ""),
                        help="Optional auth token")
    parser.add_argument("--start-cell", type=int, default=0,
                        help="Skip to this code-cell index (0-based) to resume after a failure")
    parser.add_argument("--stop-before-download", action="store_true",
                        help="Stop before the last cell (files.download) which only works in browser")
    args = parser.parse_args()

    if not args.url:
        print(__doc__)
        sys.exit(
            "\nERROR: --url is required (or set COLAB_KERNEL_URL env var).\n"
            "See the usage instructions above for how to get it from Colab."
        )

    print(f"Connecting to Colab kernel: {args.url[:60]}...")
    client = KernelWebSocketClient(
        endpoint=args.url,
        token=args.token or None,
        timeout=300,  # long timeout for heavy cells (training loop, downloads)
    )
    client.start()
    print("Connected.\n")

    cells = load_code_cells(NOTEBOOK_PATH)
    print(f"Loaded {len(cells)} code cells from {NOTEBOOK_PATH}")

    if args.start_cell:
        print(f"Skipping to cell index {args.start_cell} (--start-cell)")

    total = len(cells)
    failed_at = None

    for i, cell in enumerate(cells):
        if i < args.start_cell:
            print(f"  [skip] cell {i+1}/{total}")
            continue

        # The last cell uses google.colab.files.download() which only works in browser
        is_download_cell = "files.download" in cell["source"]
        if is_download_cell and args.stop_before_download:
            print(f"\n[Stopping before download cell (--stop-before-download)]")
            print("The model file is now in the Colab runtime. Download it manually:")
            print("  Colab left panel > Files icon > loom_engine_int8.onnx > right-click > Download")
            break
        if is_download_cell:
            print(f"\n[Cell {i+1}/{total}] Skipping files.download() cell — this only works in the browser.")
            print("Download loom_engine_int8.onnx manually from:")
            print("  Colab left panel > Files icon > loom_engine_int8.onnx > right-click > Download")
            continue

        ok = execute_cell(client, cell["source"], cell_num=i + 1, total=total)
        if not ok:
            failed_at = i
            print(f"\n[STOPPED] Cell {i+1} returned an error. Fix it and re-run with --start-cell {i}")
            break

    client.stop()

    if failed_at is None:
        print("\n✅  All cells completed successfully.")
        print("Next steps:")
        print("  1. Download loom_engine_int8.onnx from the Colab file browser")
        print("     (Files panel > loom_engine_int8.onnx > right-click > Download)")
        print("  2. Copy it into loomhash/inference/models/ (once that module is built)")
        print("  3. Update docs/open-decisions.md D-04 and docs/verification-checklist.md")
        print("     to record that a real trained artifact now exists.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

