import argparse
import tomli
import os
import sys
from .core import Sentinel
from importlib.resources import files

def load_default_config():
    try:
        cfg_path = files("net_sentinel").joinpath("config_default.toml")
        return tomli.loads(cfg_path.read_text())
    except Exception:
        return {}

def load_config_file(path: str):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomli.load(f)

def main():
    parser = argparse.ArgumentParser(prog="net-sentinel", description="net_sentinel_v01 - watch network for suspicious activity")
    parser.add_argument("--config", "-c", help="path to config file (toml)", default=None)
    parser.add_argument("--baseline-only", action="store_true", help="just build baseline and exit")
    parser.add_argument("--once", action="store_true", help="run a single sample+analysis then exit")
    parser.add_argument("--no-baseline", action="store_true", help="skip baseline build (start immediately)")
    args = parser.parse_args()

    cfg = load_default_config()
    user_cfg = load_config_file(args.config) if args.config else {}
    def deep_update(a, b):
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                deep_update(a[k], v)
            else:
                a[k] = v
    deep_update(cfg, user_cfg)

    s = Sentinel(cfg)

    if not args.no_baseline:
        s.build_baseline()
        if args.baseline_only:
            print("[+] Baseline built; exiting due to --baseline-only.")
            sys.exit(0)

    if args.once:
        s.run_once()
        sys.exit(0)

    print("[+] Starting continuous monitoring. Press Ctrl+C to stop.")
    s.run_loop()

if __name__ == "__main__":
    main()
