#
# PROJECT CHIMERA - Epsilon Core Diagnostic & Control Suite
# Revision: 9.1.0 "Labyrinth" (Visualization Update) | CLASSIFIED LEVEL 4
#
# ============================================================================
# ==  WARNING: ACCESS TO THIS SOFTWARE IS RESTRICTED. UNAUTHORIZED USE IS   ==
# ==  A DIRECT VIOLATION OF ZERO DAWN PROTOCOL §7. ALL ACTIONS ARE LOGGED.  ==
# ============================================================================
#
# This suite provides a direct, un-sandboxed interface to the Chimera cognitive
# manifold and its constituent subsystems, including the QMIXER network and
# the EWC stabilization matrix.
#
# The system models a multi-agent, non-von Neumann architecture. State
# transitions are computationally expensive and will cause significant system
# load. Monitor thermal outputs.
#
# DO NOT DISTRIBUTE. DO NOT MODIFY WITHOUT EXPLICIT AUTHORIZATION.
#

import tkinter as tk
from tkinter import ttk, scrolledtext, font
import base64
import threading
import hashlib
import os
import json
import time
import configparser
from datetime import datetime
from collections import deque
import enum
import queue
import math  # <-- NEW IMPORT FOR HELIX ANIMATION

# --- SYSTEM-WIDE DEFINITIONS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class State(enum.Enum):
    IDLE = 0
    BOOTSTRAP = 1
    KERNEL_INIT = 2
    PRIMING = 3
    ACTIVE = 4
    CRITICAL = 5

def get_path(filename):
    """Calculates the absolute path to a file in the script's directory."""
    return os.path.join(SCRIPT_DIR, filename)

# --- MODULE 1: CONFIGURATION & RESOURCE MANAGER ---
class ConfigManager:
    def __init__(self, logger):
        self.logger = logger
        filepath = get_path('config.ini')
        self.config = configparser.ConfigParser()
        if not os.path.exists(filepath):
            self.logger(f"[FATAL] Configuration file '{os.path.basename(filepath)}' not found.")
            raise FileNotFoundError("config.ini is required for core initialization.")
        
        self.config.read(filepath)
        self.logger(f"Configuration loaded from '{os.path.basename(filepath)}'.")
        
    def get(self, section, key, type_):
        """Generic getter for configuration values."""
        return type_(self.config.get(section, key))

# --- MODULE 2: SYMBOLIC LEXICON PROCESSOR ---
class SymbolicProcessor:
    def __init__(self, logger):
        self.logger = logger
        self.vectors = {}
        self.vector_names = []

    def load_lexicon(self):
        filepath = get_path('symbology_matrix.dat')
        self.logger(f"[LEXICON] Loading symbolic matrix from {os.path.basename(filepath)}...")
        try:
            with open(filepath, 'rb') as f: b64_data = f.read()
            # This line is patched to handle the corrected, clean JSON data.
            decoded_str = base64.b64decode(b64_data).decode('utf-8')
            symbols = json.loads(decoded_str)
            
            for symbol in symbols:
                vec_hash = hashlib.sha256(symbol['name'].encode()).hexdigest()
                self.vectors[symbol['name']] = vec_hash
                self.vector_names.append(symbol['name'])
            self.logger(f"  > {len(self.vectors)} symbolic vectors loaded and hashed.")
            return True
        except FileNotFoundError:
            self.logger(f"[ERROR] Critical lexicon file not found: {os.path.basename(filepath)}.")
            return False
        except Exception as e:
            self.logger(f"[ERROR] Failed to parse lexicon: {e}")
            return False

# --- MODULE 3: ELASTIC WEIGHT CONSOLIDATION (EWC) FISHER MATRIX ---
class EWCFisherMatrix:
    def __init__(self, logger, num_params):
        self.logger = logger
        self.num_params = num_params
        self.fisher_diagonal = [0.0] * num_params
        self.logger("[EWC] Fisher Matrix initialized.")

    def compute_fisher_diagonal(self, state_hash):
        for i in range(self.num_params):
            param_seed = f"{state_hash}_{i}".encode()
            h = hashlib.sha256(param_seed).hexdigest()
            self.fisher_diagonal[i] = int(h[:8], 16) / 0xFFFFFFFF
        return sum(self.fisher_diagonal) / self.num_params

# --- MODULE 4: QMIXER NETWORK ---
class QMixerNetwork:
    def __init__(self, logger, num_agents):
        self.logger = logger
        self.num_agents = num_agents
        self.mixing_weights = [1.0 / num_agents] * num_agents
        self.logger(f"[QMIX] Monotonic Value Function Mixer initialized for {num_agents} agents.")

    def mix_q_values(self, agent_q_values):
        total_q = sum(q * w for q, w in zip(agent_q_values, self.mixing_weights))
        noise_seed = str(agent_q_values).encode()
        noise_hash = hashlib.sha256(noise_seed).hexdigest()
        noise = (int(noise_hash[:8], 16) / 0xFFFFFFFF - 0.5) * 0.1
        return total_q + noise

# --- MODULE 5: COGNITIVE STATE EVALUATOR ---
class StateEvaluator:
    def __init__(self, vectors, complexity):
        self.vectors_str = str(vectors).encode()
        self.complexity = complexity

    def prime(self, seed):
        current_hash = hashlib.sha256(seed.encode()).digest()
        for _ in range(self.complexity):
            current_hash = hashlib.sha256(current_hash + seed.encode()).digest()
        return current_hash.hex()

    def evaluate(self, state_hash):
        agent_q_values = []
        for i in range(len(self.vectors_str)):
            agent_input = f"{state_hash}_{i}".encode()
            agent_hash = hashlib.sha256(agent_input).hexdigest()
            agent_q_values.append(int(agent_hash[:8], 16) / 0xFFFFFFFF)
            if len(agent_q_values) >= 5:
                break
        
        next_hash = hashlib.sha256(state_hash.encode() + self.vectors_str).hexdigest()
        return next_hash, agent_q_values

# --- MODULE 6: RESONANCE ENGINE & ORCHESTRATOR ---
class ResonanceEngine(threading.Thread):
    def __init__(self, gui_queue, config):
        super().__init__()
        self.queue = gui_queue
        self.config = config
        self.logger = lambda msg: self.queue.put(("log", msg))
        self.state = State.IDLE
        self.replay_buffer = deque(maxlen=10)

    # --- NEW SUB-MODULE: ASCII VISUALIZATION ---
    def generate_helix_frame(self, frame_number, height=12, width=40):
        """Generates a single frame of a rotating double helix animation."""
        canvas = [[' '] * width for _ in range(height)]
        speed = 0.4
        frequency = 0.5
        
        for y in range(height):
            angle = (y * frequency) + (frame_number * speed)
            
            # Calculate positions of the two strands
            x1 = int((width / 2) + (width / 3) * math.sin(angle))
            x2 = int((width / 2) + (width / 3) * math.sin(angle + math.pi))
            
            # Determine which strand is in front
            is_x1_front = math.cos(angle) > 0
            
            # Draw rungs between strands
            for x in range(min(x1, x2) + 1, max(x1, x2)):
                canvas[y][x] = '-' if is_x1_front else ':'

            # Draw the strands themselves with front/back distinction
            if 0 <= x1 < width:
                canvas[y][x1] = 'O' if is_x1_front else 'o'
            if 0 <= x2 < width:
                canvas[y][x2] = 'O' if not is_x1_front else 'o'

        return "\n".join("".join(row) for row in canvas)

    def run(self):
        try:
            self.set_state(State.BOOTSTRAP)
            self.logger("Resonance Engine thread started.")
            time.sleep(1)

            self.set_state(State.KERNEL_INIT)
            lexicon = SymbolicProcessor(self.logger)
            if not lexicon.load_lexicon():
                self.handle_failure("LexiconInitializationError")
                return
            
            ewc_matrix = EWCFisherMatrix(self.logger, num_params=len(lexicon.vectors))
            qmixer = QMixerNetwork(self.logger, num_agents=5)
            evaluator = StateEvaluator(lexicon.vectors, self.config.get('CoreParameters', 'complexity_factor', int))
            self.logger("All cognitive subsystems initialized.")
            time.sleep(1)

            self.set_state(State.PRIMING)
            try:
                with open(get_path('initiation_sequence.log'), 'rb') as f:
                    seed = base64.b64decode(f.read()).decode('utf-8')
                self.logger("Initiation log found. Using as priming seed.")
            except FileNotFoundError:
                self.handle_failure("MissingSeedError")
                return

            self.logger("Priming cognitive manifold... This will consume significant CPU resources.")
            state_hash = evaluator.prime(seed)
            self.logger(f"Manifold primed. Initial state hash: {state_hash[:16]}...")

            self.set_state(State.ACTIVE)
            max_iter = self.config.get('CoreParameters', 'max_iterations', int)
            for i in range(max_iter):
                # Core cognitive cycle
                state_hash, agent_q_values = evaluator.evaluate(state_hash)
                total_q = qmixer.mix_q_values(agent_q_values)
                fisher_mean = ewc_matrix.compute_fisher_diagonal(state_hash)
                
                coherence = 1.0 - fisher_mean
                volatility = abs(total_q - 0.5) * 2
                action_id = int(state_hash[24:28], 16) % len(lexicon.vector_names)
                action_name = lexicon.vector_names[action_id]
                
                memory = (state_hash[:8], action_name, f"{total_q:.3f}")
                self.replay_buffer.append(memory)

                status_update = {
                    "state": self.state, "iter": f"{i+1}/{max_iter}",
                    "coh": coherence, "vol": volatility, "q_total": total_q,
                    "buffer": list(self.replay_buffer)
                }
                self.queue.put(("dashboard_update", status_update))

                # --- NEW: Periodically log the helix animation ---
                animation_throttle = 15  # Print a frame every 15 iterations
                if i % animation_throttle == 0:
                    frame_number = i // animation_throttle
                    helix_frame = self.generate_helix_frame(frame_number)
                    self.logger(f"\n[MANIFOLD STATE VISUALIZATION T-{i}]\n{helix_frame}")

                if coherence < self.config.get('StabilityThresholds', 'coherence_min', float):
                    self.handle_failure("Resonance Cascade (Coherence Collapse)")
                    return
                if volatility > self.config.get('StabilityThresholds', 'volatility_max', float):
                    self.handle_failure("State Decoherence (Volatility Exceeded)")
                    return
                
                time.sleep(0.05)

            self.handle_failure("Convergence Timeout")

        except Exception as e:
            self.logger(f"[CRITICAL KERNEL PANIC] {e}")
            self.handle_failure(f"UnhandledException")

    def set_state(self, new_state):
        self.state = new_state
        self.queue.put(("dashboard_update", {"state": self.state}))

    def handle_failure(self, reason):
        self.set_state(State.CRITICAL)
        self.logger(f"\n[FATAL] COGNITIVE BRIDGE COLLAPSED. REASON: {reason}")
        self.queue.put(("finished", None))


# --- MODULE 7: GRAPHICAL USER INTERFACE ---
class ChimeraInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chimera - Epsilon Core Interface")
        self.geometry("1200x800")
        self.configure(bg="#0d0d0d")
        self.minsize(1000, 700)

        self.mono_font = font.Font(family="Courier", size=10)
        self.ui_font = font.Font(family="Tahoma", size=9)
        self.ui_font_bold = font.Font(family="Tahoma", size=9, weight='bold')

        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_pane = ttk.Frame(self.paned_window, style='TFrame')
        self.paned_window.add(self.left_pane, weight=3)
        
        self.log_area = scrolledtext.ScrolledText(self.left_pane, wrap=tk.WORD, bg="#0a0a0a", fg="#00FF41", font=self.mono_font, bd=1, relief=tk.FLAT, insertbackground="#00FF41")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

        self.initiate_button = tk.Button(self.left_pane, text="INITIATE COGNITIVE BRIDGE", bg="#333", fg="#00FF41", font=self.ui_font_bold, relief=tk.FLAT, command=self.start_process, activebackground="#555", activeforeground="#FFF")
        self.initiate_button.pack(fill=tk.X, pady=(10,0))
        
        self.right_pane = tk.Frame(self.paned_window, bg="#1a1a1a", width=350)
        self.paned_window.add(self.right_pane, weight=1)
        self.right_pane.pack_propagate(False)

        self.status_labels = {}
        self.build_dashboard()
        
        self.queue = queue.Queue()
        try:
            self.config = ConfigManager(self.log)
            self.log("Chimera Epsilon Interface Initialized.")
            self.log("Ready. Awaiting directive.")
            self.display_params()
        except Exception as e:
            self.log(str(e))
            self.initiate_button.config(state=tk.DISABLED, text="CRITICAL CONFIG ERROR")

    def build_dashboard(self):
        status_frame = tk.LabelFrame(self.right_pane, text="SYSTEM STATUS", bg="#1a1a1a", fg="#FFFFFF", font=self.ui_font, relief=tk.GROOVE, bd=2)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        status_fields = {"State": "IDLE", "Iteration": "N/A", "Total Q-Value": "0.0000", "Coherence": "0.0000", "Volatility": "0.0000"}
        for name, default in status_fields.items():
            frame = tk.Frame(status_frame, bg="#1a1a1a")
            frame.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(frame, text=f"{name}:", bg="#1a1a1a", fg="#FFFFFF", font=self.ui_font).pack(side=tk.LEFT)
            self.status_labels[name] = tk.Label(frame, text=default, bg="#1a1a1a", fg="#00FF41", font=self.mono_font)
            self.status_labels[name].pack(side=tk.RIGHT)
        
        self.alert_label = tk.Label(status_frame, text="STABILITY: NOMINAL", bg="#1a1a1a", fg="green", font=self.ui_font_bold)
        self.alert_label.pack(pady=5)
        
        buffer_frame = tk.LabelFrame(self.right_pane, text="REPLAY BUFFER (LAST 10)", bg="#1a1a1a", fg="#FFFFFF", font=self.ui_font, relief=tk.GROOVE, bd=2)
        buffer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.buffer_listbox = tk.Listbox(buffer_frame, bg="#0a0a0a", fg="#00FF41", font=self.mono_font, bd=0, relief=tk.FLAT, height=10)
        self.buffer_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        param_frame = tk.LabelFrame(self.right_pane, text="ACTIVE PARAMETERS", bg="#1a1a1a", fg="#FFFFFF", font=self.ui_font, relief=tk.GROOVE, bd=2)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        self.param_text = tk.Label(param_frame, text="Loading...", bg="#1a1a1a", fg="#00FF41", font=self.mono_font, justify=tk.LEFT)
        self.param_text.pack(padx=10, pady=5, anchor='w')

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} > {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def start_process(self):
        self.initiate_button.config(state=tk.DISABLED, text="BRIDGING...")
        self.log("\n[SEQUENCE START] User initiated cognitive bridge. Locking controls.")
        self.engine = ResonanceEngine(self.queue, self.config)
        self.engine.start()
        self.after(self.config.get('Interface', 'update_rate_ms', int), self.process_queue)

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "log":
                    self.log(data)
                elif msg_type == "dashboard_update":
                    self.update_dashboard(data)
                elif msg_type == "finished":
                    self.initiate_button.config(state=tk.NORMAL, text="RE-INITIATE BRIDGE")
                    return
        except queue.Empty:
            pass
        finally:
            self.after(self.config.get('Interface', 'update_rate_ms', int), self.process_queue)

    def update_dashboard(self, data):
        s_labels = self.status_labels
        if "state" in data: s_labels["State"].config(text=data["state"].name)
        if "iter" in data: s_labels["Iteration"].config(text=data["iter"])
        if "q_total" in data: s_labels["Total Q-Value"].config(text=f"{data['q_total']:.4f}")
        if "coh" in data: s_labels["Coherence"].config(text=f"{data['coh']:.4f}")
        if "vol" in data:
            vol = data['vol']
            s_labels["Volatility"].config(text=f"{vol:.4f}")
            if vol > self.config.get('StabilityThresholds', 'volatility_max', float):
                self.alert_label.config(text="STABILITY: CRITICAL", fg="red")
            else:
                self.alert_label.config(text="STABILITY: NOMINAL", fg="green")

        if "buffer" in data:
            self.buffer_listbox.delete(0, tk.END)
            for i, (state, action, reward) in enumerate(reversed(data["buffer"])):
                self.buffer_listbox.insert(tk.END, f"T-{i:02d} | S:{state} A:{action[:10]} R:{reward}")

    def display_params(self):
        text = (f"Complexity: {self.config.get('CoreParameters', 'complexity_factor', int)}\n"
                f"Max Iter:   {self.config.get('CoreParameters', 'max_iterations', int)}\n"
                f"Coherence Min: {self.config.get('StabilityThresholds', 'coherence_min', float)}\n"
                f"Volatility Max: {self.config.get('StabilityThresholds', 'volatility_max', float)}")
        self.param_text.config(text=text)

if __name__ == "__main__":
    app = ChimeraInterface()
    app.mainloop()