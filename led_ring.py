# led_ring.py
# Contrôleur non-bloquant pour anneau WS2812B (NeoPixel) sur Raspberry Pi
# Dépendances: rpi_ws281x, adafruit-circuitpython-neopixel
#   pip3 install rpi_ws281x adafruit-circuitpython-neopixel

import time
import threading
from dataclasses import dataclass, field

try:
    import board
    import neopixel
except Exception as e:
    raise RuntimeError(
        "Libs NeoPixel manquantes. Installe: pip3 install rpi_ws281x adafruit-circuitpython-neopixel"
    ) from e


def _clamp(x, lo=0, hi=255):
    return max(lo, min(hi, int(x)))


def _scale(color, s: float):
    r, g, b = color
    return (_clamp(r * s), _clamp(g * s), _clamp(b * s))


COL_RED    = (255,  20,  20)
COL_GREEN  = ( 20, 255,  60)
COL_BLUE   = ( 30, 140, 255)
COL_WHITE  = (255, 255, 255)
COL_AMBER  = (255, 160,  40)
COL_OFF    = (  0,   0,   0)

@dataclass
class LedRing:
    led_count: int = 24
    pin: object = board.D18               # GPIO18 (pin 12) recommandé
    brightness: float = 0.4               # luminosité globale (0..1)
    auto_write: bool = False              # on contrôle show() nous-mêmes
    pixel_order: str = "GRB"              # GRB pour WS2812B
    power_limit_ma: int = 1000            # limite logicielle (sécurité)
    _pixels: neopixel.NeoPixel = field(init=False, repr=False)
    _th: threading.Thread = field(init=False, default=None, repr=False)
    _stop: threading.Event = field(init=False, default_factory=threading.Event, repr=False)
    _lock: threading.Lock = field(init=False, default_factory=threading.Lock, repr=False)
    _mode: str = field(init=False, default="idle", repr=False)
    _mode_args: dict = field(init=False, default_factory=dict, repr=False)
    _last_t: float = field(init=False, default_factory=time.time, repr=False)
    _phase: float = field(init=False, default=0.0, repr=False)
    _countdown_total: float = field(init=False, default=3.0, repr=False)
    _countdown_start: float = field(init=False, default=0.0, repr=False)
    _spinner_pos: float = field(init=False, default=0.0, repr=False)

    def __post_init__(self):
        order = getattr(neopixel, self.pixel_order) if isinstance(self.pixel_order, str) else self.pixel_order
        self._pixels = neopixel.NeoPixel(
            self.pin, self.led_count, brightness=self.brightness,
            auto_write=self.auto_write, pixel_order=order
        )
        self.clear()
        self._th = threading.Thread(target=self._run, name="LedRingThread", daemon=True)
        self._th.start()

    # ----------------- API publique -----------------

    def idle(self):
        self._set_mode("idle")

    def countdown(self, seconds: int = 3):
        with self._lock:
            self._mode = "countdown"
            self._mode_args = {}
            self._countdown_total = max(1, int(seconds))
            self._countdown_start = time.time()

    def flash(self, duration: float = 0.13):
        self._set_mode("flash", duration=duration)

    def saving(self):
        self._set_mode("saving")

    def success(self, hold: float = 0.6):
        self._set_mode("success", hold=hold)

    def error(self, hold: float = 0.8):
        self._set_mode("error", hold=hold)

    def fill(self, color):
        self._pixels.fill(color)
        self._pixels.show()

    def clear(self):
        self.fill(COL_OFF)

    def close(self):
        self._stop.set()
        if self._th and self._th.is_alive():
            self._th.join(timeout=1.0)
        self.clear()
        try:
            self._pixels.deinit()
        except Exception:
            pass

    # ----------------- Interne: moteur d’animation -----------------

    def _set_mode(self, mode, **kwargs):
        with self._lock:
            self._mode = mode
            self._mode_args = kwargs
            self._phase = 0.0
            self._last_t = time.time()

    def _run(self):
        target_fps = 60.0
        frame_time = 1.0 / target_fps
        while not self._stop.is_set():
            t = time.time()
            dt = t - self._last_t
            self._last_t = t
            try:
                with self._lock:
                    mode = self._mode
                    args = dict(self._mode_args)  # copy for thread-safety

                if mode == "idle":
                    self._anim_idle(dt)
                elif mode == "countdown":
                    self._anim_countdown()
                elif mode == "flash":
                    done = self._anim_flash(args.get("duration", 0.13))
                    if done:
                        self._set_mode("idle")
                elif mode == "saving":
                    self._anim_saving(dt)
                elif mode == "success":
                    done = self._anim_solid(COL_GREEN, args.get("hold", 0.6))
                    if done:
                        self._set_mode("idle")
                elif mode == "error":
                    done = self._anim_pulse(COL_RED, 2.0, total= args.get("hold", 0.8))
                    if done:
                        self._set_mode("idle")
                else:
                    self._anim_idle(dt)

                # sécurité power limit (approx, simple scaling)
                self._apply_power_limit()

                self._pixels.show()
            except Exception:
                # En cas de souci, on évite de crasher le thread
                pass
            time.sleep(frame_time)

    # ----------------- Effets -----------------

    def _anim_idle(self, dt):
        # respiration douce ambre
        self._phase = (self._phase + dt) % 2.0
        s = 0.5 + 0.5 * (1.0 - abs((self._phase * 2) - 1))  # triangle 0..1..0
        color = _scale(COL_AMBER, 0.15 + 0.35 * s)
        self._pixels.fill(color)

    def _anim_countdown(self):
        elapsed = time.time() - self._countdown_start
        remaining = max(0.0, self._countdown_total - elapsed)
        frac = remaining / self._countdown_total  # 1 -> 0
        lit = int(round(frac * self.led_count))

        # Anneau rempli en vert qui se vide vers 0
        for i in range(self.led_count):
            self._pixels[i] = COL_GREEN if i < lit else (20, 40, 20)

        # à chaque seconde franchie: éclat bref
        step_left = int(remaining + 0.9999)
        if step_left > 0 and abs(remaining - step_left) < 0.08:
            # petit blink blanc
            for i in range(self.led_count):
                if i % 2 == 0:
                    self._pixels[i] = _scale(COL_WHITE, 0.6)

        if remaining <= 0.0:
            # bascule automatique sur flash (déclenchement)
            self._set_mode("flash", duration=0.12)

    def _anim_flash(self, duration: float):
        # plein blanc puis extinction sur durée
        since = (time.time() - self._last_t)  # micro-delta; on veut un vrai chrono
        # On préfère un timestamp d’entrée de mode:
        if "_flash_t0" not in self._mode_args:
            with self._lock:
                self._mode_args["_flash_t0"] = time.time()
        t0 = self._mode_args["_flash_t0"]
        elapsed = time.time() - t0
        k = max(0.0, 1.0 - (elapsed / max(0.01, duration)))
        self._pixels.fill(_scale(COL_WHITE, 0.25 + 0.75 * k))
        return elapsed >= duration

    def _anim_saving(self, dt):
        # spinner bleu + queue
        speed = 8.0  # tours/seconde (visuel vif)
        self._spinner_pos = (self._spinner_pos + speed * dt) % self.led_count
        head = int(self._spinner_pos)
        trail = 6
        for i in range(self.led_count):
            d = (i - head) % self.led_count
            if d == 0:
                self._pixels[i] = COL_WHITE
            elif d <= trail:
                self._pixels[i] = _scale(COL_BLUE, (trail - d) / trail * 0.9)
            else:
                self._pixels[i] = _scale(COL_BLUE, 0.05)

    def _anim_solid(self, color, hold):
        # affiche une couleur unie pour hold secondes
        if "_solid_t0" not in self._mode_args:
            with self._lock:
                self._mode_args["_solid_t0"] = time.time()
        t0 = self._mode_args["_solid_t0"]
        self._pixels.fill(color)
        return (time.time() - t0) >= hold

    def _anim_pulse(self, color, freq_hz=2.0, total=0.8):
        if "_pulse_t0" not in self._mode_args:
            with self._lock:
                self._mode_args["_pulse_t0"] = time.time()
        t0 = self._mode_args["_pulse_t0"]
        elapsed = time.time() - t0
        s = 0.5 + 0.5 * (1.0 + __import__("math").sin(2 * __import__("math").pi * freq_hz * elapsed)) / 2
        self._pixels.fill(_scale(color, 0.1 + 0.9 * s))
        return elapsed >= total

    def _apply_power_limit(self):
        """Réduit globalement si on dépasse ~power_limit_ma (approx naïve)."""
        # Hypothèse: chaque canal à 255 ≈ 20mA/LED -> 60mA/LED blanc.
        # On estime le total courant ~ somme(R+G+B)/765 * 60mA par LED
        tot = 0
        for i in range(self.led_count):
            r, g, b = self._pixels[i]
            tot += (r + g + b)
        # courant estimé en mA:
        cur = (tot / 765.0) * 60.0
        cur *= (self.led_count / max(1, self.led_count))  # cohérence
        if cur > self.power_limit_ma:
            # scale down
            scale = self.power_limit_ma / max(1e-6, cur)
            for i in range(self.led_count):
                r, g, b = self._pixels[i]
                self._pixels[i] = (_clamp(r * scale), _clamp(g * scale), _clamp(b * scale))
