"""BANKER'S ALGORITHM SIMULATOR
MODULES:
    - calculate_need()     : Computes the Need matrix from Max - Allocation
    - is_safe()            : Runs the Safety Algorithm to find a safe sequence
    - request_resources()  : Handles a process resource request with rollback
    - detect_deadlock()    : Detects deadlocked processes in the current state
    - BankersGUI class     : Full Tkinter GUI wrapping all above functions
=============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import copy


# ─────────────────────────────────────────────────────────────────────────────
#  CORE ALGORITHM FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_need(max_matrix, allocation_matrix, n_processes, n_resources):

    need_matrix = []
    for i in range(n_processes):
        row = []
        for j in range(n_resources):
            val = max_matrix[i][j] - allocation_matrix[i][j]
            if val < 0:
                return None, (
                    f"Error: Allocation[{i}][{j}] > Max[{i}][{j}]. "
                    "Allocation cannot exceed Maximum."
                )
            row.append(val)
        need_matrix.append(row)
    return need_matrix, ""


def is_safe(allocation_matrix, need_matrix, available, n_processes, n_resources):
    """
    Banker's Safety Algorithm.

    """
    work = list(available)          # Work vector (copy of Available)
    finish = [False] * n_processes  # Finish flags for each process
    safe_sequence = []
    steps = []

    steps.append(f"Initial Work (Available): {work}")

    while True:
        found = False
        for i in range(n_processes):
            if not finish[i]:
                # Check if Need[i] <= Work (process can be satisfied)
                can_allocate = all(
                    need_matrix[i][j] <= work[j] for j in range(n_resources)
                )
                if can_allocate:
                    # Simulate process completion: release its resources
                    steps.append(
                        f"  P{i}: Need={need_matrix[i]} ≤ Work={work} → "
                        f"GRANT. Work becomes {[work[j] + allocation_matrix[i][j] for j in range(n_resources)]}"
                    )
                    for j in range(n_resources):
                        work[j] += allocation_matrix[i][j]
                    finish[i] = True
                    safe_sequence.append(i)
                    found = True
                    break  # Restart search from P0 after each grant

        if not found:
            break  

    all_finished = all(finish)
    if all_finished:
        steps.append(f"\n SAFE STATE — Safe Sequence: {['P'+str(p) for p in safe_sequence]}")
    else:
        deadlocked = [f"P{i}" for i in range(n_processes) if not finish[i]]
        steps.append(f"\n UNSAFE STATE — Deadlocked Processes: {deadlocked}")

    return all_finished, safe_sequence, steps


def request_resources(process_id, request, allocation_matrix, need_matrix,
                      available, n_processes, n_resources):
    """
    Resource Request Algorithm (Banker's).
    """
    steps = []
    pid = process_id

    # Step 1: Validate request does not exceed declared need
    for j in range(n_resources):
        if request[j] > need_matrix[pid][j]:
            msg = (
                f" REJECTED: Request[{j}]={request[j]} exceeds "
                f"Need[P{pid}][{j}]={need_matrix[pid][j]}.\n"
                "Process has exceeded its maximum claim."
            )
            return False, msg, steps

    # Step 2: Check if resources are currently available
    for j in range(n_resources):
        if request[j] > available[j]:
            msg = (
                f" BLOCKED: Request[{j}]={request[j]} exceeds "
                f"Available[{j}]={available[j]}.\n"
                "P{pid} must wait — resources not available right now."
            )
            return False, msg, steps

    steps.append(f"P{pid} request {request} passes validation checks.")
    steps.append("Tentatively allocating resources...")

    # Step 3: Tentative allocation (deep copies for rollback)
    old_available = list(available)
    old_allocation = copy.deepcopy(allocation_matrix)
    old_need = copy.deepcopy(need_matrix)

    for j in range(n_resources):
        available[j] -= request[j]
        allocation_matrix[pid][j] += request[j]
        need_matrix[pid][j] -= request[j]

    steps.append(f"  Available  : {old_available} → {available}")
    steps.append(f"  Alloc[P{pid}]: {old_allocation[pid]} → {allocation_matrix[pid]}")
    steps.append(f"  Need[P{pid}] : {old_need[pid]} → {need_matrix[pid]}")

    # Step 4: Run safety check on new state
    safe, seq, safety_steps = is_safe(
        allocation_matrix, need_matrix, available, n_processes, n_resources
    )
    steps.extend(safety_steps)

    if safe:
        # Step 5a: Keep allocation — system is still safe
        msg = (
            f" APPROVED: Request by P{pid} granted.\n"
            f"Safe Sequence: {['P'+str(p) for p in seq]}"
        )
        return True, msg, steps
    else:
        # Step 5b: Rollback — restoring previous state
        for j in range(n_resources):
            available[j] = old_available[j]
        for i in range(n_processes):
            allocation_matrix[i] = old_allocation[i][:]
            need_matrix[i] = old_need[i][:]

        steps.append("\nRolling back — restoring previous state.")
        msg = (
            f" REJECTED: Granting P{pid}'s request would lead to UNSAFE state.\n"
            "Allocation rolled back. Process must wait."
        )
        return False, msg, steps


def detect_deadlock(allocation_matrix, need_matrix, available, n_processes, n_resources):
    """
    Deadlock Detection Algorithm.

    """
    safe, seq, steps = is_safe(
        allocation_matrix, need_matrix, available, n_processes, n_resources
    )

    if safe:
        return False, [], steps
    else:
        completed = set(seq)
        deadlocked = [i for i in range(n_processes) if i not in completed]
        return True, deadlocked, steps


# ─────────────────────────────────────────────────────────────────────────────
#  GUI CLASS
# ─────────────────────────────────────────────────────────────────────────────

class BankersGUI:

    CLR_BG        = "#0d1117"   # Dark background
    CLR_PANEL     = "#161b22"   # Card/panel background
    CLR_BORDER    = "#30363d"   # Border color
    CLR_TEXT      = "#e6edf3"   # Primary text
    CLR_MUTED     = "#8b949e"   # Secondary text
    CLR_SAFE      = "#238636"   # Green for safe
    CLR_SAFE_LT   = "#2ea043"   # Lighter green
    CLR_UNSAFE    = "#da3633"   # Red for unsafe/deadlock
    CLR_UNSAFE_LT = "#f85149"   # Lighter red
    CLR_ACCENT    = "#1f6feb"   # Blue accent
    CLR_ACCENT_LT = "#388bfd"   # Lighter blue
    CLR_WARN      = "#d29922"   # Yellow warning
    CLR_INPUT_BG  = "#0d1117"   # Input field background
    CLR_INPUT_FG  = "#c9d1d9"   # Input field text

    def __init__(self, root):
        self.root = root
        self.root.title("Banker's Algorithm — Deadlock Detection & Avoidance")
        self.root.configure(bg=self.CLR_BG)
        self.root.geometry("1280x820")
        self.root.minsize(1100, 700)

        # State variables
        self.n_proc      = tk.IntVar(value=5)
        self.n_res       = tk.IntVar(value=3)
        self.alloc_entries = []
        self.max_entries   = []
        self.avail_entries = []
        self.req_proc_var  = tk.IntVar(value=0)

        # Algorithm data (populated after "Calculate Need")
        self.allocation  = []
        self.maximum     = []
        self.available   = []
        self.need        = []

        self._build_ui()
        self._load_test_case_1()   # Pre-load a safe-state example

    # ── UI Construction

    def _build_ui(self):
        """Assemble all UI sections."""
        self._build_title()

        # Main two-column layout
        main = tk.Frame(self.root, bg=self.CLR_BG)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=4)
        main.rowconfigure(0, weight=1)

        left  = tk.Frame(main, bg=self.CLR_BG)
        right = tk.Frame(main, bg=self.CLR_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right.grid(row=0, column=1, sticky="nsew")

        self._build_config_panel(left)
        self._build_matrix_input(left)
        self._build_request_panel(left)
        self._build_buttons(left)
        self._build_output_panel(right)

    def _build_title(self):
        """Title bar with gradient-style look."""
        bar = tk.Frame(self.root, bg=self.CLR_ACCENT, height=3)
        bar.pack(fill=tk.X)

        hdr = tk.Frame(self.root, bg=self.CLR_PANEL, pady=10)
        hdr.pack(fill=tk.X, padx=0)

        tk.Label(hdr, text="🏦  BANKER'S ALGORITHM",
                 font=("Courier New", 18, "bold"),
                 bg=self.CLR_PANEL, fg=self.CLR_ACCENT_LT).pack(side=tk.LEFT, padx=20)

        tk.Label(hdr, text="Deadlock Detection & Avoidance Simulator",
                 font=("Courier New", 10),
                 bg=self.CLR_PANEL, fg=self.CLR_MUTED).pack(side=tk.LEFT)

        self.status_label = tk.Label(hdr, text="● IDLE",
                                     font=("Courier New", 11, "bold"),
                                     bg=self.CLR_PANEL, fg=self.CLR_MUTED)
        self.status_label.pack(side=tk.RIGHT, padx=20)

    def _card(self, parent, title):
        """Helper: create a titled card frame."""
        outer = tk.Frame(parent, bg=self.CLR_BORDER, bd=0)
        outer.pack(fill=tk.X, pady=4)

        inner = tk.Frame(outer, bg=self.CLR_PANEL, padx=10, pady=8)
        inner.pack(fill=tk.X, padx=1, pady=1)

        tk.Label(inner, text=title, font=("Courier New", 9, "bold"),
                 bg=self.CLR_PANEL, fg=self.CLR_ACCENT_LT).pack(anchor="w", pady=(0, 5))
        return inner

    def _build_config_panel(self, parent):
        """Processes & resources count inputs."""
        card = self._card(parent, "⚙  SYSTEM CONFIGURATION")

        row = tk.Frame(card, bg=self.CLR_PANEL)
        row.pack(fill=tk.X)

        for label, var in [("Processes:", self.n_proc), ("Resource Types:", self.n_res)]:
            f = tk.Frame(row, bg=self.CLR_PANEL)
            f.pack(side=tk.LEFT, padx=(0, 20))
            tk.Label(f, text=label, font=("Courier New", 9),
                     bg=self.CLR_PANEL, fg=self.CLR_TEXT).pack(side=tk.LEFT)
            sb = tk.Spinbox(f, from_=1, to=10, width=4, textvariable=var,
                            bg=self.CLR_INPUT_BG, fg=self.CLR_INPUT_FG,
                            insertbackground=self.CLR_TEXT,
                            buttonbackground=self.CLR_BORDER,
                            relief=tk.FLAT, font=("Courier New", 10))
            sb.pack(side=tk.LEFT, padx=5)

        tk.Button(card, text="Rebuild Matrices",
                  command=self._rebuild_matrices,
                  bg=self.CLR_ACCENT, fg="white",
                  font=("Courier New", 9, "bold"),
                  relief=tk.FLAT, padx=8, pady=3,
                  cursor="hand2").pack(anchor="w", pady=(6, 0))

    def _build_matrix_input(self, parent):
        """Scrollable frame containing Allocation, Max, and Available entry grids."""
        self.matrix_card = self._card(parent, "📋  INPUT MATRICES")
        self._rebuild_matrices()

    def _rebuild_matrices(self):
        """Destroy & recreate entry grids based on current n_proc / n_res."""
        # Clear old widgets inside matrix_card (skip title label)
        for w in self.matrix_card.winfo_children():
            if isinstance(w, tk.Label) and "INPUT" in (w.cget("text") or ""):
                continue
            if not (isinstance(w, tk.Label) and w.cget("fg") == self.CLR_ACCENT_LT):
                w.destroy()

        # Clear any child frames
        for w in list(self.matrix_card.winfo_children()):
            if isinstance(w, tk.Frame):
                w.destroy()

        n = self.n_proc.get()
        r = self.n_res.get()

        self.alloc_entries = []
        self.max_entries   = []
        self.avail_entries = []

        # Column headers
        def header_row(parent, n_res, label):
            hf = tk.Frame(parent, bg=self.CLR_PANEL)
            hf.pack(fill=tk.X, pady=(8, 2))
            tk.Label(hf, text=label, font=("Courier New", 8, "bold"),
                     bg=self.CLR_PANEL, fg=self.CLR_WARN, width=14, anchor="w").pack(side=tk.LEFT)
            for j in range(n_res):
                tk.Label(hf, text=f"R{j}", width=5, font=("Courier New", 8),
                         bg=self.CLR_PANEL, fg=self.CLR_MUTED).pack(side=tk.LEFT)

        def matrix_rows(parent, n_proc, n_res, store):
            for i in range(n_proc):
                rf = tk.Frame(parent, bg=self.CLR_PANEL)
                rf.pack(fill=tk.X, pady=1)
                tk.Label(rf, text=f"P{i}", width=14, font=("Courier New", 8),
                         bg=self.CLR_PANEL, fg=self.CLR_MUTED, anchor="w").pack(side=tk.LEFT)
                row_entries = []
                for j in range(n_res):
                    e = tk.Entry(rf, width=5, bg=self.CLR_INPUT_BG, fg=self.CLR_INPUT_FG,
                                 insertbackground=self.CLR_TEXT, relief=tk.FLAT,
                                 font=("Courier New", 9), justify="center",
                                 highlightthickness=1,
                                 highlightbackground=self.CLR_BORDER,
                                 highlightcolor=self.CLR_ACCENT)
                    e.insert(0, "0")
                    e.pack(side=tk.LEFT, padx=2)
                    row_entries.append(e)
                store.append(row_entries)

        # ── Allocation Matrix ──
        header_row(self.matrix_card, r, "ALLOCATION →")
        matrix_rows(self.matrix_card, n, r, self.alloc_entries)

        # ── Maximum Matrix ──
        header_row(self.matrix_card, r, "MAXIMUM →")
        matrix_rows(self.matrix_card, n, r, self.max_entries)

        # ── Available Vector ──
        avf = tk.Frame(self.matrix_card, bg=self.CLR_PANEL)
        avf.pack(fill=tk.X, pady=(10, 2))
        tk.Label(avf, text="AVAILABLE →", font=("Courier New", 8, "bold"),
                 bg=self.CLR_PANEL, fg=self.CLR_WARN, width=14, anchor="w").pack(side=tk.LEFT)
        for j in range(r):
            e = tk.Entry(avf, width=5, bg=self.CLR_INPUT_BG, fg=self.CLR_INPUT_FG,
                         insertbackground=self.CLR_TEXT, relief=tk.FLAT,
                         font=("Courier New", 9), justify="center",
                         highlightthickness=1,
                         highlightbackground=self.CLR_BORDER,
                         highlightcolor=self.CLR_ACCENT)
            e.insert(0, "0")
            e.pack(side=tk.LEFT, padx=2)
            self.avail_entries.append(e)

    def _build_request_panel(self, parent):
        """Resource request input section."""
        card = self._card(parent, "  RESOURCE REQUEST")

        row1 = tk.Frame(card, bg=self.CLR_PANEL)
        row1.pack(fill=tk.X)
        tk.Label(row1, text="Process ID (P):", font=("Courier New", 9),
                 bg=self.CLR_PANEL, fg=self.CLR_TEXT).pack(side=tk.LEFT)
        tk.Spinbox(row1, from_=0, to=9, width=4, textvariable=self.req_proc_var,
                   bg=self.CLR_INPUT_BG, fg=self.CLR_INPUT_FG,
                   buttonbackground=self.CLR_BORDER,
                   relief=tk.FLAT, font=("Courier New", 10)).pack(side=tk.LEFT, padx=6)

        row2 = tk.Frame(card, bg=self.CLR_PANEL)
        row2.pack(fill=tk.X, pady=4)
        tk.Label(row2, text="Request Vector:", font=("Courier New", 9),
                 bg=self.CLR_PANEL, fg=self.CLR_TEXT).pack(side=tk.LEFT)
        self.req_entry = tk.Entry(row2, width=20, bg=self.CLR_INPUT_BG, fg=self.CLR_INPUT_FG,
                                  insertbackground=self.CLR_TEXT, relief=tk.FLAT,
                                  font=("Courier New", 9),
                                  highlightthickness=1,
                                  highlightbackground=self.CLR_BORDER,
                                  highlightcolor=self.CLR_ACCENT)
        self.req_entry.insert(0, "1 0 2")
        self.req_entry.pack(side=tk.LEFT, padx=6)
        tk.Label(row2, text="(space-separated)", font=("Courier New", 8),
                 bg=self.CLR_PANEL, fg=self.CLR_MUTED).pack(side=tk.LEFT)

    def _build_buttons(self, parent):
        """Action buttons row."""
        bf = tk.Frame(parent, bg=self.CLR_BG, pady=6)
        bf.pack(fill=tk.X)

        buttons = [
            ("Calculate Need",    self.CLR_ACCENT,   self._do_calculate_need),
            ("Check Safe State",  self.CLR_SAFE,     self._do_check_safe),
            ("Request Resource",  self.CLR_WARN,     self._do_request),
            ("Detect Deadlock",   self.CLR_UNSAFE,   self._do_detect),
            ("Reset System",      self.CLR_BORDER,   self._do_reset),
        ]

        for text, color, cmd in buttons:
            tk.Button(bf, text=text, command=cmd,
                      bg=color, fg="white",
                      font=("Courier New", 9, "bold"),
                      relief=tk.FLAT, padx=10, pady=5,
                      cursor="hand2",
                      activebackground=self.CLR_ACCENT_LT,
                      activeforeground="white").pack(side=tk.LEFT, padx=3)

        # Test case loader buttons
        tc_frame = tk.Frame(parent, bg=self.CLR_BG, pady=2)
        tc_frame.pack(fill=tk.X)
        tk.Label(tc_frame, text="Load Test Case:", font=("Courier New", 8),
                 bg=self.CLR_BG, fg=self.CLR_MUTED).pack(side=tk.LEFT, padx=(3, 6))

        for i, (label, fn) in enumerate([
            ("1-Safe",    self._load_test_case_1),
            ("2-Unsafe",  self._load_test_case_2),
            ("3-Deadlock",self._load_test_case_3),
        ], 1):
            tk.Button(tc_frame, text=label, command=fn,
                      bg=self.CLR_PANEL, fg=self.CLR_MUTED,
                      font=("Courier New", 8),
                      relief=tk.FLAT, padx=6, pady=3,
                      cursor="hand2").pack(side=tk.LEFT, padx=2)

    def _build_output_panel(self, parent):
        """Right-side output: log + matrix display."""
        # Status banner
        self.banner = tk.Label(parent, text="",
                               font=("Courier New", 13, "bold"),
                               bg=self.CLR_PANEL, fg=self.CLR_TEXT,
                               pady=10, relief=tk.FLAT)
        self.banner.pack(fill=tk.X, pady=(0, 4))

        # Notebook for tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.TNotebook",
                        background=self.CLR_BG,
                        borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
                        background=self.CLR_PANEL,
                        foreground=self.CLR_MUTED,
                        font=("Courier New", 9),
                        padding=[12, 5])
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", self.CLR_ACCENT)],
                  foreground=[("selected", "white")])

        nb = ttk.Notebook(parent, style="Dark.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Execution Log
        log_tab = tk.Frame(nb, bg=self.CLR_PANEL)
        nb.add(log_tab, text="  Execution Log  ")
        self.log = scrolledtext.ScrolledText(
            log_tab, wrap=tk.WORD,
            bg=self.CLR_INPUT_BG, fg=self.CLR_TEXT,
            font=("Courier New", 9),
            insertbackground=self.CLR_TEXT,
            relief=tk.FLAT, padx=10, pady=8,
            selectbackground=self.CLR_ACCENT,
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Color tags for log
        self.log.tag_config("safe",   foreground=self.CLR_SAFE_LT)
        self.log.tag_config("unsafe", foreground=self.CLR_UNSAFE_LT)
        self.log.tag_config("info",   foreground=self.CLR_ACCENT_LT)
        self.log.tag_config("warn",   foreground=self.CLR_WARN)
        self.log.tag_config("muted",  foreground=self.CLR_MUTED)
        self.log.tag_config("head",   foreground=self.CLR_TEXT,
                            font=("Courier New", 10, "bold"))

        # Tab 2: Matrices
        mat_tab = tk.Frame(nb, bg=self.CLR_PANEL)
        nb.add(mat_tab, text="  Matrices  ")
        self.matrix_display = scrolledtext.ScrolledText(
            mat_tab, wrap=tk.NONE,
            bg=self.CLR_INPUT_BG, fg=self.CLR_TEXT,
            font=("Courier New", 10),
            relief=tk.FLAT, padx=10, pady=8,
        )
        self.matrix_display.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    # ── Helper methods ─────────────────────────────────────────────────────

    def _log(self, text, tag=""):
        """Append a line to the log widget."""
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n", tag)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _log_sep(self, char="─", tag="muted"):
        self._log(char * 60, tag)

    def _clear_log(self):
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def _set_banner(self, text, color):
        self.banner.configure(text=text, bg=color,
                               fg="white" if color != self.CLR_PANEL else self.CLR_TEXT)
        self.status_label.configure(text=f"● {text[:30]}", fg=color)

    def _parse_matrix(self, entries, n_proc, n_res, name):
        """Parse a 2D entry grid into a list of lists with validation."""
        mat = []
        for i in range(n_proc):
            row = []
            for j in range(n_res):
                val = entries[i][j].get().strip()
                if val == "":
                    raise ValueError(f"{name}[{i}][{j}] is empty.")
                v = int(val)
                if v < 0:
                    raise ValueError(f"{name}[{i}][{j}]={v} is negative.")
                row.append(v)
            mat.append(row)
        return mat

    def _parse_available(self, n_res):
        """Parse the Available resource vector."""
        avail = []
        for j, e in enumerate(self.avail_entries[:n_res]):
            val = e.get().strip()
            if val == "":
                raise ValueError(f"Available[{j}] is empty.")
            v = int(val)
            if v < 0:
                raise ValueError(f"Available[{j}]={v} is negative.")
            avail.append(v)
        return avail

    def _display_matrices(self):
        """Render all matrices in the Matrices tab."""
        n = len(self.allocation)
        r = len(self.available)
        self.matrix_display.configure(state=tk.NORMAL)
        self.matrix_display.delete("1.0", tk.END)

        def fmt_row(label, row):
            return f"  {label:<6} | " + "  ".join(f"{v:3}" for v in row)

        def section(title, mat):
            out = f"\n{'─'*50}\n  {title}\n{'─'*50}\n"
            out += "         | " + "  ".join(f" R{j}" for j in range(r)) + "\n"
            for i, row in enumerate(mat):
                out += fmt_row(f"P{i}", row) + "\n"
            return out

        text = section("ALLOCATION MATRIX", self.allocation)
        text += section("MAXIMUM MATRIX", self.maximum)
        if self.need:
            text += section("NEED MATRIX  (Max - Allocation)", self.need)
        text += f"\n{'─'*50}\n  AVAILABLE RESOURCES\n{'─'*50}\n"
        text += "         | " + "  ".join(f" R{j}" for j in range(r)) + "\n"
        text += fmt_row("", self.available) + "\n"

        self.matrix_display.insert(tk.END, text)
        self.matrix_display.configure(state=tk.DISABLED)

    def _read_inputs(self):
        """Read all input matrices and store in self.*"""
        n = self.n_proc.get()
        r = self.n_res.get()
        self.allocation = self._parse_matrix(self.alloc_entries, n, r, "Allocation")
        self.maximum    = self._parse_matrix(self.max_entries,   n, r, "Maximum")
        self.available  = self._parse_available(r)

    # ── Button Actions ─────────────────────────────────────────────────────

    def _do_calculate_need(self):
        """Calculate Need Matrix and display it."""
        self._clear_log()
        self._log_sep("═")
        self._log("  CALCULATE NEED MATRIX", "head")
        self._log_sep("═")
        try:
            self._read_inputs()
            n, r = self.n_proc.get(), self.n_res.get()
            need, err = calculate_need(self.maximum, self.allocation, n, r)
            if need is None:
                self._log(f"\n{err}", "unsafe")
                self._set_banner(" Input Error", self.CLR_WARN)
                return
            self.need = need
            self._log("\nNeed Matrix = Maximum − Allocation\n", "info")
            self._log(f"  {'Process':<8} | Need", "info")
            self._log("  " + "─"*30, "muted")
            for i, row in enumerate(self.need):
                self._log(f"  P{i:<7} | {row}", "")
            self._log("\n Need matrix calculated successfully.", "safe")
            self._display_matrices()
            self._set_banner("Need Matrix Ready", self.CLR_ACCENT)
        except ValueError as e:
            self._log(f"\n Input Error: {e}", "unsafe")
            messagebox.showerror("Input Error", str(e))

    def _do_check_safe(self):
        """Run the Safety Algorithm."""
        self._clear_log()
        self._log_sep("═")
        self._log("  BANKER'S SAFETY ALGORITHM", "head")
        self._log_sep("═")

        if not self.need:
            self._log("\n  Please calculate Need Matrix first.", "warn")
            return

        n, r = self.n_proc.get(), self.n_res.get()
        safe, seq, steps = is_safe(
            self.allocation, self.need, list(self.available), n, r
        )
        self._log("\nStep-by-step execution:\n", "info")
        for s in steps:
            if "✅" in s:
                self._log(s, "safe")
            elif "❌" in s:
                self._log(s, "unsafe")
            else:
                self._log(s, "")

        if safe:
            self._log_sep()
            self._log(f"\n🟢 SYSTEM IS IN SAFE STATE", "safe")
            self._log(f"   Safe Sequence: {' → '.join('P'+str(p) for p in seq)}", "safe")
            self._set_banner("🟢 SAFE STATE", self.CLR_SAFE)
        else:
            self._log_sep()
            self._log("\n🔴 SYSTEM IS IN UNSAFE STATE", "unsafe")
            self._log("   Deadlock may occur!", "unsafe")
            self._set_banner("🔴 UNSAFE STATE", self.CLR_UNSAFE)

    def _do_request(self):
        """Handle a resource request from a process."""
        self._clear_log()
        self._log_sep("═")
        self._log("  RESOURCE REQUEST ALGORITHM", "head")
        self._log_sep("═")

        if not self.need:
            self._log("\n  Please calculate Need Matrix first.", "warn")
            return

        try:
            pid = self.req_proc_var.get()
            n   = self.n_proc.get()
            r   = self.n_res.get()

            if pid < 0 or pid >= n:
                raise ValueError(f"Process ID {pid} is out of range [0, {n-1}].")

            req_str = self.req_entry.get().strip().split()
            if len(req_str) != r:
                raise ValueError(f"Request must have {r} values, got {len(req_str)}.")
            request = [int(x) for x in req_str]
            if any(x < 0 for x in request):
                raise ValueError("Request values cannot be negative.")

            self._log(f"\nProcess P{pid} requests: {request}\n", "info")

            # Work on deep copies so we can show rollback clearly
            alloc_copy = copy.deepcopy(self.allocation)
            need_copy  = copy.deepcopy(self.need)
            avail_copy = list(self.available)

            approved, msg, steps = request_resources(
                pid, request, alloc_copy, need_copy, avail_copy, n, r
            )

            for s in steps:
                self._log(s, "")

            self._log_sep()
            if approved:
                # Commit changes
                self.allocation = alloc_copy
                self.need       = need_copy
                self.available  = avail_copy
                self._log(f"\n{msg}", "safe")
                self._set_banner(" Request Approved", self.CLR_SAFE)
                self._display_matrices()
            else:
                self._log(f"\n{msg}", "unsafe")
                self._set_banner(" Request Denied", self.CLR_UNSAFE)

        except ValueError as e:
            self._log(f"\n Input Error: {e}", "unsafe")
            messagebox.showerror("Input Error", str(e))

    def _do_detect(self):
        """Run deadlock detection."""
        self._clear_log()
        self._log_sep("═")
        self._log("  DEADLOCK DETECTION", "head")
        self._log_sep("═")

        if not self.need:
            self._log("\n  Please calculate Need Matrix first.", "warn")
            return

        n, r = self.n_proc.get(), self.n_res.get()
        deadlock, deadlocked, steps = detect_deadlock(
            self.allocation, self.need, list(self.available), n, r
        )

        for s in steps:
            self._log(s, "")

        self._log_sep()
        if deadlock:
            self._log(f"\n🔴 DEADLOCK DETECTED!", "unsafe")
            self._log(f"   Deadlocked Processes: {['P'+str(d) for d in deadlocked]}", "unsafe")
            self._log("\n   These processes cannot proceed and are waiting", "unsafe")
            self._log("   for resources held by each other.", "unsafe")
            self._set_banner("🔴 DEADLOCK DETECTED", self.CLR_UNSAFE)
        else:
            self._log("\n🟢 NO DEADLOCK — System is in safe state.", "safe")
            self._set_banner("🟢 No Deadlock", self.CLR_SAFE)

    def _do_reset(self):
        """Reset all data and clear output."""
        self._clear_log()
        self.allocation = []
        self.maximum    = []
        self.available  = []
        self.need       = []
        self._rebuild_matrices()
        self.matrix_display.configure(state=tk.NORMAL)
        self.matrix_display.delete("1.0", tk.END)
        self.matrix_display.configure(state=tk.DISABLED)
        self.banner.configure(text="", bg=self.CLR_PANEL)
        self._set_banner("IDLE", self.CLR_MUTED)
        self._log("System reset. Enter new values.", "muted")

    # ── Test Case Loaders ──────────────────────────────────────────────────

    def _fill_matrix(self, entries, data):
        """Fill a 2D entry grid with given data."""
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                entries[i][j].delete(0, tk.END)
                entries[i][j].insert(0, str(val))

    def _fill_avail(self, data):
        """Fill the Available vector entries."""
        for j, e in enumerate(self.avail_entries):
            e.delete(0, tk.END)
            e.insert(0, str(data[j]) if j < len(data) else "0")

    def _load_test_case_1(self):
        """
        TEST CASE 1 — SAFE STATE (Classic Dijkstra Example)
        Expected safe sequence: P1 → P3 → P4 → P0 → P2
        """
        self.n_proc.set(5)
        self.n_res.set(3)
        self._rebuild_matrices()

        alloc = [[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]]
        max_  = [[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]]
        avail = [3, 3, 2]

        self._fill_matrix(self.alloc_entries, alloc)
        self._fill_matrix(self.max_entries,   max_)
        self._fill_avail(avail)
        self.need = []
        self._set_banner("Test Case 1 Loaded (Safe)", self.CLR_ACCENT)
        self._clear_log()
        self._log("Test Case 1 — Safe State Loaded", "info")
        self._log("Expected safe sequence: P1 → P3 → P4 → P0 → P2", "muted")
        self._log('Press "Calculate Need" then "Check Safe State"', "muted")

    def _load_test_case_2(self):
        """
        TEST CASE 2 — UNSAFE STATE
        Modified so no safe sequence exists.
        """
        self.n_proc.set(4)
        self.n_res.set(3)
        self._rebuild_matrices()

        alloc = [[2,1,0],[1,0,1],[0,1,0],[1,1,1]]
        max_  = [[3,2,1],[2,1,2],[1,2,1],[2,2,2]]
        avail = [0, 0, 0]   # No available resources → unsafe

        self._fill_matrix(self.alloc_entries, alloc)
        self._fill_matrix(self.max_entries,   max_)
        self._fill_avail(avail)
        self.need = []
        self._set_banner("Test Case 2 Loaded (Unsafe)", self.CLR_WARN)
        self._clear_log()
        self._log("Test Case 2 — Unsafe State Loaded", "warn")
        self._log("Available = [0,0,0] → system likely unsafe", "muted")
        self._log('Press "Calculate Need" then "Check Safe State"', "muted")

    def _load_test_case_3(self):
        """
        TEST CASE 3 — DEADLOCK
        All processes waiting; none can proceed.
        """
        self.n_proc.set(3)
        self.n_res.set(2)
        self._rebuild_matrices()

        alloc = [[1,0],[0,1],[1,1]]
        max_  = [[2,2],[2,2],[2,2]]
        avail = [0, 0]

        self._fill_matrix(self.alloc_entries, alloc)
        self._fill_matrix(self.max_entries,   max_)
        self._fill_avail(avail)
        self.need = []
        self._set_banner("Test Case 3 Loaded (Deadlock)", self.CLR_UNSAFE)
        self._clear_log()
        self._log("Test Case 3 — Deadlock Case Loaded", "unsafe")
        self._log("All processes waiting, no resources available", "muted")
        self._log('Press "Calculate Need" then "Detect Deadlock"', "muted")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Main entry point — launches the Tkinter GUI."""
    root = tk.Tk()
    app  = BankersGUI(root)

    # Center window on screen
    root.update_idletasks()
    w = root.winfo_width()


    
    h = root.winfo_height()
    x = (root.winfo_screenwidth()  - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()
