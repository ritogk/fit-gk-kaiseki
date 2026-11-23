"""ESP32 (hibeam_live) とのシリアル接続。切断されても自動で再接続する。"""
import glob
import re
import threading
import time

import serial

from . import config


def find_port():
    if config.SERIAL_PORT:
        return config.SERIAL_PORT
    ports = sorted(glob.glob("/dev/cu.usbmodem*"))
    return ports[0] if ports else None


class SerialLink:
    def __init__(self):
        self.ser = None
        self.port = None
        self.last_line = ""
        self.lock = threading.Lock()
        self._stop = False
        self._closing = False
        self._sent = {"r": None, "l": None}
        self._params = {"f": None, "g": None}
        threading.Thread(target=self._reader, daemon=True).start()

    @property
    def connected(self):
        return self.ser is not None

    def _open(self):
        port = find_port()
        if not port:
            return False
        try:
            # dsrdtr/rtscts を切り、開いたときに ESP32 がリセットされないようにする
            s = serial.Serial()
            s.port, s.baudrate, s.timeout, s.write_timeout = port, config.BAUD, 0, 0.2
            s.dtr = False
            s.rts = False
            s.open()
        except (serial.SerialException, OSError):
            return False
        self.ser, self.port = s, port
        self._sent = {"r": None, "l": None}
        self._params = {"f": None, "g": None}
        self.write(f"t{config.RUN_FADE_MS}")
        return True

    def _drop(self):
        try:
            if self.ser:
                self.ser.close()
        except Exception:
            pass
        self.ser = None

    def _reader(self):
        buf = b""
        while not self._stop:
            if self.ser is None:
                if not self._open():
                    time.sleep(1.0)
                    continue
            try:
                data = self.ser.read(4096)
            except (serial.SerialException, OSError, TypeError):
                with self.lock:
                    self._drop()
                continue
            if data:
                buf += data
                *lines, buf = buf.split(b"\n")
                if lines:
                    self.last_line = lines[-1].decode(errors="replace").strip()
                    self._check_fade(self.last_line)
            else:
                time.sleep(0.01)

    def _check_fade(self, line):
        """ESP32 が再起動するとフェードが 300ms に戻るため、ずれていたら送り直す。"""
        m = re.search(r"fade=(\d+)ms", line)
        if m and not self._closing and int(m.group(1)) != config.RUN_FADE_MS:
            self.write(f"t{config.RUN_FADE_MS}")
            self._sent = {"r": None, "l": None}
            self._params = {"f": None, "g": None}

    def write(self, cmd):
        with self.lock:
            if self.ser is None:
                return False
            try:
                self.ser.write((cmd + "\n").encode())
                return True
            except (serial.SerialException, OSError):
                self._drop()
                return False

    def set_lr(self, r, l):
        """変化があったチャンネルだけ送る(0.1%単位)。"""
        for key, v in (("r", r), ("l", l)):
            v = round(max(0.0, min(100.0, v)), 1)
            if self._sent[key] != v:
                if self.write(f"{key}{v:.1f}"):
                    self._sent[key] = v

    def set_params(self, freq, gamma):
        """PWM周波数とガンマを、変化があったときだけ送る。"""
        for key, v, cmd in (("f", freq, f"f{int(freq)}"), ("g", gamma, f"g{gamma:.2f}")):
            if self._params[key] != v:
                if self.write(cmd):
                    self._params[key] = v

    def shutdown(self):
        self._closing = True
        self.write(f"t{config.IDLE_FADE_MS}")
        self.write("0")
        time.sleep(0.1)
        self._stop = True
        with self.lock:
            self._drop()
