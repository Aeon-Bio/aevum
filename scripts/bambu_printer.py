"""LAN-mode client for a Bambu Lab printer: status, live watch, SD upload, and
(only with --yes-print) starting a plate.

Credentials come from a config file outside the repo (default
~/.config/aevum/bambu_h2s.json with host, serial, access_code) or from the
BAMBU_HOST / BAMBU_SERIAL / BAMBU_ACCESS_CODE environment variables.  Never
commit the access code.

H2-series firmware (H2D/H2S, and X1/P1 from 2025 firmware on) enforces
"Authorization Control": with Developer Mode OFF on the printer touchscreen,
status reads work but every MQTT command answers
{"result": "failed", "reason": "mqtt message verify failed", "err_code": 84033543}
and FTPS logs in but denies every directory listing and upload (553).  Turn on
Settings > General > Developer Mode on the printer before using load/purge/
upload/print.

Commands:
  status                 one full state report (read-only)
  watch [--log FILE]     stream state changes until Ctrl-C (read-only)
  upload FILE...         copy .gcode.3mf files to the printer SD card (no print)
  files                  list .3mf files on the SD card
  print FILE --yes-print start a print of an uploaded file (explicit opt-in)
  load --tray N          run the printer's own load-and-purge from AMS tray N (0 = A1)
  purge --mm 30          heat the nozzle and extrude extra filament through it
  unload                 retract the loaded filament back into the AMS
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path.home() / ".config" / "aevum" / "bambu_h2s.json"

STATE_KEYS = (
    "gcode_state", "mc_percent", "mc_remaining_time", "layer_num", "total_layer_num",
    "subtask_name", "gcode_file", "nozzle_temper", "nozzle_target_temper", "bed_temper",
    "bed_target_temper", "chamber_temper", "cooling_fan_speed", "big_fan1_speed",
    "print_error", "print_type", "wifi_signal", "spd_lvl", "stg_cur", "print_gcode_action",
)


def load_config(path: Path | None) -> dict[str, str]:
    cfg: dict[str, Any] = {}
    p = path or DEFAULT_CONFIG
    if p.exists():
        cfg = json.loads(p.read_text())
    for key, env in (("host", "BAMBU_HOST"), ("serial", "BAMBU_SERIAL"), ("access_code", "BAMBU_ACCESS_CODE")):
        if os.environ.get(env):
            cfg[key] = os.environ[env]
    missing = [k for k in ("host", "serial", "access_code") if not cfg.get(k)]
    if missing:
        sys.exit(f"missing printer config: {', '.join(missing)} (file {p} or env vars)")
    return cfg


# ------------------------------------------------------------------ MQTT

class Printer:
    def __init__(self, cfg: dict[str, str]):
        import paho.mqtt.client as mqtt  # imported lazily so upload/files work without it

        self.cfg = cfg
        self.state: dict[str, Any] = {}
        self.updates: list[dict[str, Any]] = []
        self._event = threading.Event()
        self._lock = threading.Lock()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"aevum-{int(time.time())}", protocol=mqtt.MQTTv311)
        self.client.username_pw_set("bblp", cfg["access_code"])
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # printer presents a self-signed cert
        self.client.tls_set_context(ctx)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.connected = threading.Event()
        self.connect_rc: int | None = None

    @property
    def report_topic(self) -> str:
        return f"device/{self.cfg['serial']}/report"

    @property
    def request_topic(self) -> str:
        return f"device/{self.cfg['serial']}/request"

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self.connect_rc = int(reason_code.value) if hasattr(reason_code, "value") else int(reason_code)
        if self.connect_rc == 0:
            client.subscribe(self.report_topic)
        self.connected.set()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            return
        report = payload.get("print")
        if not isinstance(report, dict):
            return
        with self._lock:
            self.state.update(report)
            self.updates.append(report)
        self._event.set()

    def connect(self, timeout: float = 10.0) -> None:
        self.client.connect_async(self.cfg["host"], 8883, keepalive=30)
        self.client.loop_start()
        if not self.connected.wait(timeout):
            self.client.loop_stop()
            sys.exit(f"MQTT: no response from {self.cfg['host']}:8883 within {timeout:.0f}s")
        if self.connect_rc != 0:
            self.client.loop_stop()
            sys.exit(f"MQTT: connection refused (reason {self.connect_rc}); check the access code")

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def request(self, body: dict[str, Any]) -> None:
        self.client.publish(self.request_topic, json.dumps(body), qos=1)

    def pushall(self) -> None:
        self.request({"pushing": {"sequence_id": "0", "command": "pushall", "version": 1, "push_target": 1}})

    def wait_update(self, timeout: float) -> bool:
        got = self._event.wait(timeout)
        self._event.clear()
        return got

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self.state)


def summarize(state: dict[str, Any]) -> dict[str, Any]:
    out = {k: state.get(k) for k in STATE_KEYS if k in state}
    hms = state.get("hms")
    if hms:
        out["hms"] = hms
    ams = state.get("ams")
    if isinstance(ams, dict):
        out["ams_units"] = len(ams.get("ams", []))
    return out


def one_line(state: dict[str, Any]) -> str:
    s = state
    rem = s.get("mc_remaining_time")
    rem_txt = f"{int(rem) // 60}h{int(rem) % 60:02d}m left" if isinstance(rem, (int, float)) else "?"
    return (
        f"{datetime.now().strftime('%H:%M:%S')} {s.get('gcode_state', '?'):<8} {s.get('mc_percent', '?'):>3}% "
        f"layer {s.get('layer_num', '?')}/{s.get('total_layer_num', '?')} {rem_txt} | "
        f"nozzle {s.get('nozzle_temper', '?')}/{s.get('nozzle_target_temper', '?')} bed {s.get('bed_temper', '?')}/{s.get('bed_target_temper', '?')} "
        f"chamber {s.get('chamber_temper', '?')} | {s.get('subtask_name') or s.get('gcode_file') or '-'}"
        + (f" | ERROR {s.get('print_error')}" if s.get("print_error") else "")
    )


# ------------------------------------------------------------------ FTPS

def _curl_ftps(cfg: dict[str, str], args: list[str]) -> subprocess.CompletedProcess[str]:
    base = ["/usr/bin/curl", "--silent", "--show-error", "--insecure", "--ftp-pasv", "-u", f"bblp:{cfg['access_code']}"]
    return subprocess.run(base + args, capture_output=True, text=True, check=False)


def list_files(cfg: dict[str, str]) -> list[str]:
    r = _curl_ftps(cfg, [f"ftps://{cfg['host']}:990/"])
    if r.returncode != 0:
        sys.exit(f"FTPS list failed ({r.returncode}): {r.stderr.strip()}")
    return [line for line in r.stdout.splitlines() if line.strip()]


def upload(cfg: dict[str, str], files: list[Path]) -> None:
    for f in files:
        if not f.exists():
            sys.exit(f"missing file: {f}")
        if not f.name.endswith(".gcode.3mf"):
            sys.exit(f"{f.name}: only sliced .gcode.3mf files are uploaded")
        size_mb = f.stat().st_size / 1e6
        print(f"uploading {f.name} ({size_mb:.1f} MB) ...", flush=True)
        r = _curl_ftps(cfg, ["-T", str(f), f"ftps://{cfg['host']}:990/{f.name}"])
        if r.returncode != 0:
            sys.exit(f"upload failed for {f.name} ({r.returncode}): {r.stderr.strip()}")
    print("uploaded", len(files), "file(s); nothing was started")


# ------------------------------------------------------------------ commands

def cmd_status(cfg: dict[str, str], as_json: bool) -> None:
    p = Printer(cfg)
    p.connect()
    p.pushall()
    deadline = time.time() + 8
    while time.time() < deadline:
        p.wait_update(1.0)
        if "gcode_state" in p.state:
            break
    state = p.snapshot()
    p.close()
    if not state:
        sys.exit("connected, but the printer sent no report; is it in LAN mode with the access code current?")
    if as_json:
        print(json.dumps(summarize(state), indent=1))
    else:
        print(one_line(state))
        for k, v in summarize(state).items():
            if k not in ("gcode_state", "mc_percent", "layer_num", "total_layer_num", "mc_remaining_time"):
                print(f"  {k}: {v}")


def cmd_watch(cfg: dict[str, str], log: Path | None, state_file: Path | None, interval: float) -> None:
    p = Printer(cfg)
    p.connect()
    p.pushall()
    last_line = None
    try:
        while True:
            p.wait_update(interval)
            state = p.snapshot()
            if not state:
                continue
            line = one_line(state)
            if line[9:] != (last_line or "")[9:]:
                print(line, flush=True)
                if log:
                    with log.open("a") as fh:
                        fh.write(line + "\n")
                last_line = line
            if state_file:
                state_file.write_text(json.dumps({"updated": datetime.now().isoformat(timespec="seconds"), **summarize(state)}, indent=1))
    except KeyboardInterrupt:
        pass
    finally:
        p.close()


def cmd_print(cfg: dict[str, str], name: str, yes: bool, bed_leveling: bool, flow_cali: bool, tray: int = 0) -> None:
    if not yes:
        sys.exit("refusing to start a print without --yes-print")
    if not name.endswith(".gcode.3mf"):
        sys.exit("give the uploaded .gcode.3mf file name")
    p = Printer(cfg)
    p.connect()
    p.pushall()
    p.wait_update(3.0)
    state = p.snapshot()
    if state.get("gcode_state") in ("RUNNING", "PAUSE", "PREPARE"):
        p.close()
        sys.exit(f"printer is {state.get('gcode_state')}; not starting another job")
    body = {
        "print": {
            "sequence_id": "0", "command": "project_file", "param": "Metadata/plate_1.gcode",
            "url": f"file:///sdcard/{name}", "subtask_name": name.replace(".gcode.3mf", ""),
            "use_ams": True, "ams_mapping": [tray], "timelapse": False, "bed_leveling": bed_leveling, "flow_cali": flow_cali,
            "vibration_cali": False, "layer_inspect": False, "bed_type": "textured_plate",
        }
    }
    p.request(body)
    print("start command sent for", name)
    deadline = time.time() + 20
    while time.time() < deadline:
        p.wait_update(1.0)
        s = p.snapshot()
        if s.get("gcode_state") in ("RUNNING", "PREPARE"):
            print(one_line(s))
            break
    p.close()


def _tray_label(idx: int) -> str:
    return f"{'ABCD'[idx // 4]}{idx % 4 + 1}"


def cmd_load(cfg: dict[str, str], tray: int, temp: int) -> None:
    p = Printer(cfg)
    p.connect()
    p.pushall()
    p.wait_update(3.0)
    s = p.snapshot()
    if s.get("gcode_state") not in ("IDLE", "FINISH", "FAILED"):
        p.close()
        sys.exit(f"printer is {s.get('gcode_state')}; not touching the filament path")
    trays = {int(t["id"]) + 4 * int(u["id"]): t for u in s.get("ams", {}).get("ams", []) for t in u.get("tray", [])}
    t = trays.get(tray)
    if not t or not t.get("tray_type"):
        p.close()
        sys.exit(f"tray {_tray_label(tray)} is empty or unknown; trays seen: {[(_tray_label(k), v.get('tray_type')) for k, v in trays.items()]}")
    print(f"loading {_tray_label(tray)} ({t.get('tray_type')}, colour #{str(t.get('tray_color', ''))[:6]}) at {temp} C ...", flush=True)
    # H2-series firmware answers errno -6 unless ams_id/slot_id accompany target.
    p.request({"print": {"sequence_id": "0", "command": "ams_change_filament", "target": tray, "ams_id": tray // 4, "slot_id": tray % 4, "curr_temp": temp, "tar_temp": temp}})
    deadline = time.time() + 240
    last = None
    while time.time() < deadline:
        p.wait_update(2.0)
        s = p.snapshot()
        ams = s.get("ams", {})
        line = f"{datetime.now().strftime('%H:%M:%S')} tray_now={ams.get('tray_now')} ams_status={s.get('ams_status')} nozzle {s.get('nozzle_temper')}/{s.get('nozzle_target_temper')} state={s.get('gcode_state')} err={s.get('print_error')}"
        if line[9:] != (last or "")[9:]:
            print(line, flush=True); last = line
        if str(ams.get("tray_now")) == str(tray) and s.get("ams_status") in (0, 768, None) and time.time() > deadline - 225:
            print(f"filament from {_tray_label(tray)} is loaded"); break
    p.close()


def cmd_purge(cfg: dict[str, str], mm: float, temp: int) -> None:
    p = Printer(cfg)
    p.connect()
    p.pushall()
    p.wait_update(3.0)
    s = p.snapshot()
    if s.get("gcode_state") not in ("IDLE", "FINISH", "FAILED"):
        p.close()
        sys.exit(f"printer is {s.get('gcode_state')}; not sending gcode")
    if str(s.get("ams", {}).get("tray_now")) in ("255", "None"):
        p.close()
        sys.exit("no filament is loaded to the extruder; run `load --tray N` first")
    gcode = f"M109 S{temp}\nG92 E0\nG1 E{mm:.1f} F150\nG92 E0\nM104 S0\n"
    print(f"purging {mm:.0f} mm at {temp} C ...", flush=True)
    p.request({"print": {"sequence_id": "0", "command": "gcode_line", "param": gcode}})
    deadline = time.time() + 180
    last = None
    while time.time() < deadline:
        p.wait_update(2.0)
        s = p.snapshot()
        line = f"{datetime.now().strftime('%H:%M:%S')} nozzle {s.get('nozzle_temper')}/{s.get('nozzle_target_temper')} state={s.get('gcode_state')} err={s.get('print_error')}"
        if line[9:] != (last or "")[9:]:
            print(line, flush=True); last = line
        if s.get("nozzle_target_temper") == 0 and time.time() > deadline - 150 and float(s.get("nozzle_temper") or 0) >= temp - 15:
            print("purge gcode finished (nozzle heater off)"); break
    p.close()


def cmd_unload(cfg: dict[str, str], temp: int) -> None:
    p = Printer(cfg)
    p.connect()
    p.pushall()
    p.wait_update(3.0)
    s = p.snapshot()
    if s.get("gcode_state") not in ("IDLE", "FINISH", "FAILED"):
        p.close()
        sys.exit(f"printer is {s.get('gcode_state')}; not touching the filament path")
    p.request({"print": {"sequence_id": "0", "command": "ams_change_filament", "target": 255, "ams_id": 255, "slot_id": 255, "curr_temp": temp, "tar_temp": temp}})
    print("unload command sent")
    p.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status"); s.add_argument("--json", action="store_true")
    w = sub.add_parser("watch"); w.add_argument("--log", type=Path); w.add_argument("--state-file", type=Path); w.add_argument("--interval", type=float, default=2.0)
    u = sub.add_parser("upload"); u.add_argument("files", nargs="+", type=Path)
    sub.add_parser("files")
    pr = sub.add_parser("print"); pr.add_argument("name"); pr.add_argument("--yes-print", action="store_true")
    pr.add_argument("--no-bed-leveling", action="store_true"); pr.add_argument("--flow-cali", action="store_true")
    pr.add_argument("--tray", type=int, default=0, help="AMS tray index to print from (0 = A1)")
    ld = sub.add_parser("load"); ld.add_argument("--tray", type=int, required=True); ld.add_argument("--temp", type=int, default=220)
    pg = sub.add_parser("purge"); pg.add_argument("--mm", type=float, default=30.0); pg.add_argument("--temp", type=int, default=215)
    ul = sub.add_parser("unload"); ul.add_argument("--temp", type=int, default=220)
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.cmd == "status":
        cmd_status(cfg, args.json)
    elif args.cmd == "watch":
        cmd_watch(cfg, args.log, args.state_file, args.interval)
    elif args.cmd == "upload":
        upload(cfg, args.files)
    elif args.cmd == "files":
        for line in list_files(cfg):
            print(line)
    elif args.cmd == "print":
        cmd_print(cfg, args.name, args.yes_print, not args.no_bed_leveling, args.flow_cali, args.tray)
    elif args.cmd == "load":
        cmd_load(cfg, args.tray, args.temp)
    elif args.cmd == "purge":
        cmd_purge(cfg, args.mm, args.temp)
    elif args.cmd == "unload":
        cmd_unload(cfg, args.temp)


if __name__ == "__main__":
    main()
