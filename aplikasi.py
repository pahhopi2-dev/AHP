"""
Aplikasi Sistem Pendukung Keputusan dengan metode Analytical Hierarchy Process.
Jalankan menggunakan: python aplikasi.py
Dependensi: Python 3 dan NumPy.
"""

import random
import tkinter as tk
from fractions import Fraction
from tkinter import messagebox, ttk

import numpy as np


# Random Index (RI) Saaty untuk ukuran matriks 1 sampai 15.
RANDOM_INDEX = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
    11: 1.51,
    12: 1.48,
    13: 1.56,
    14: 1.57,
    15: 1.59,
}

SAATY_VALUES = tuple(
    [float(value) for value in range(1, 10)]
    + [1.0 / value for value in range(2, 10)]
)


class AHPApplication:
    """Mengelola antarmuka, data, dan perhitungan AHP."""

    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Sistem Pendukung Keputusan - Metode AHP")
        self.root.geometry("1100x760")
        self.root.minsize(860, 600)

        # Data contoh ditampilkan sejak awal agar aplikasi langsung siap dicoba.
        self.criteria = ["Harga", "Kualitas", "Garansi"]
        self.alternatives = ["Produk A", "Produk B", "Produk C"]
        self.matrix_vars = {}
        self._suspend_matrix_updates = False
        self._calculation_pending = False

        # Gaya dasar agar tampilan tab dan tabel lebih mudah dibaca.
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=25)

        self._build_interface()
        self._refresh_setup_lists()
        self._rebuild_matrices()
        # Langsung tampilkan hasil contoh saat aplikasi pertama kali dibuka.
        self.tabs.select(self.results_tab)

    def _build_interface(self):
        """Membuat judul aplikasi dan tiga tab alur kerja."""
        header = ttk.Frame(self.root, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Sistem Pendukung Keputusan - Analytical Hierarchy Process",
            style="Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Data contoh dan hasil AHP dihitung otomatis. Matriks dapat diubah atau diisi ulang.",
        ).pack(anchor="w", pady=(4, 0))

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.setup_tab = ttk.Frame(self.tabs, padding=14)
        self.matrix_tab = ttk.Frame(self.tabs, padding=12)
        self.results_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.setup_tab, text="1. Setup")
        self.tabs.add(self.matrix_tab, text="2. Matriks Perbandingan")
        self.tabs.add(self.results_tab, text="3. Hasil & Perankingan")

        self._build_setup_tab()
        self._build_matrix_tab()
        self._build_results_tab()

    def _build_setup_tab(self):
        """Membuat form untuk menambah dan menghapus kriteria/alternatif."""
        self.setup_tab.columnconfigure((0, 1), weight=1)
        self.setup_tab.rowconfigure(1, weight=1)

        ttk.Label(
            self.setup_tab,
            text="Masukkan minimal satu kriteria dan satu alternatif.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        criteria_frame = ttk.LabelFrame(
            self.setup_tab, text="Daftar Kriteria", padding=12
        )
        criteria_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        criteria_frame.columnconfigure(0, weight=1)
        criteria_frame.rowconfigure(1, weight=1)
        self.criteria_input = ttk.Entry(criteria_frame)
        self.criteria_input.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))
        self.criteria_input.bind("<Return>", lambda _event: self._add_item("criteria"))
        ttk.Button(
            criteria_frame,
            text="Tambah",
            command=lambda: self._add_item("criteria"),
        ).grid(row=0, column=1, sticky="ew", pady=(0, 8))
        self.criteria_list = tk.Listbox(criteria_frame, height=12, exportselection=False)
        self.criteria_list.grid(row=1, column=0, columnspan=2, sticky="nsew")
        ttk.Button(
            criteria_frame,
            text="Hapus Kriteria Terpilih",
            command=lambda: self._remove_item("criteria"),
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        alternatives_frame = ttk.LabelFrame(
            self.setup_tab, text="Daftar Alternatif", padding=12
        )
        alternatives_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        alternatives_frame.columnconfigure(0, weight=1)
        alternatives_frame.rowconfigure(1, weight=1)
        self.alternative_input = ttk.Entry(alternatives_frame)
        self.alternative_input.grid(
            row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 8)
        )
        self.alternative_input.bind(
            "<Return>", lambda _event: self._add_item("alternatives")
        )
        ttk.Button(
            alternatives_frame,
            text="Tambah",
            command=lambda: self._add_item("alternatives"),
        ).grid(row=0, column=1, sticky="ew", pady=(0, 8))
        self.alternative_list = tk.Listbox(
            alternatives_frame, height=12, exportselection=False
        )
        self.alternative_list.grid(row=1, column=0, columnspan=2, sticky="nsew")
        ttk.Button(
            alternatives_frame,
            text="Hapus Alternatif Terpilih",
            command=lambda: self._remove_item("alternatives"),
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Label(
            self.setup_tab,
            text=(
                "Perubahan daftar akan membangun ulang matriks. "
                "Matriks contoh dan hasil akan diperbarui otomatis."
            ),
            wraplength=900,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Button(
            self.setup_tab,
            text="Reset ke Data Contoh",
            command=self._reset_sample_data,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_matrix_tab(self):
        """Membuat area matriks dan tombol pengisian otomatis."""
        controls = ttk.Frame(self.matrix_tab)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(
            controls,
            text="Isi skala Saaty: 1–9 atau kebalikannya (contoh: 1/3).",
        ).pack(side="left")
        ttk.Button(
            controls,
            text="Isi Nilai Otomatis",
            command=self._autofill_matrices,
        ).pack(side="right")

        self.matrix_notebook = ttk.Notebook(self.matrix_tab)
        self.matrix_notebook.pack(fill="both", expand=True)

    def _build_results_tab(self):
        """Membuat tabel hasil bobot, konsistensi, dan peringkat."""
        self.results_tab.columnconfigure(0, weight=1)
        self.results_tab.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.results_tab)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(
            toolbar,
            text="Hitung AHP dan Perankingan",
            command=self._calculate,
        ).pack(side="left")
        ttk.Label(
            toolbar,
            text="CR ≤ 0,10 berarti konsisten; matriks berukuran 1 atau 2 selalu konsisten.",
        ).pack(side="left", padx=12)
        self.result_status = ttk.Label(
            self.results_tab,
            text="Hasil dihitung otomatis dari data dan matriks saat ini.",
            wraplength=900,
        )
        self.result_status.grid(row=2, column=0, sticky="w", pady=(8, 0))

        content = ttk.Panedwindow(self.results_tab, orient="vertical")
        content.grid(row=1, column=0, sticky="nsew")
        upper = ttk.Frame(content)
        lower = ttk.Frame(content)
        content.add(upper, weight=1)
        content.add(lower, weight=2)
        upper.columnconfigure(0, weight=1)
        upper.columnconfigure(1, weight=1)
        upper.rowconfigure(1, weight=1)
        lower.columnconfigure(0, weight=1)
        lower.rowconfigure(0, weight=1)

        ttk.Label(upper, text="Peringkat Alternatif", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.ranking_table = self._create_tree(
            upper,
            columns=("rank", "alternative", "score"),
            headings=("Peringkat", "Alternatif", "Skor Global"),
            widths=(90, 220, 120),
            row=1,
            column=0,
        )

        ttk.Label(upper, text="Bobot Prioritas Kriteria", style="Heading.TLabel").grid(
            row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 5)
        )
        self.criteria_weights_table = self._create_tree(
            upper,
            columns=("criterion", "weight"),
            headings=("Kriteria", "Bobot"),
            widths=(220, 120),
            row=1,
            column=1,
            padx=(12, 0),
        )

        self.detail_notebook = ttk.Notebook(lower)
        self.detail_notebook.grid(row=0, column=0, sticky="nsew")
        consistency_frame = ttk.Frame(self.detail_notebook, padding=6)
        self.detail_notebook.add(consistency_frame, text="Uji Konsistensi")
        self.consistency_table = self._create_tree(
            consistency_frame,
            columns=("matrix", "lambda", "ci", "cr", "status"),
            headings=("Matriks", "Lambda Maks", "CI", "CR", "Status"),
            widths=(250, 115, 100, 100, 130),
            row=0,
            column=0,
        )

    @staticmethod
    def _create_tree(
        parent, columns, headings, widths, row, column, padx=(0, 0)
    ):
        """Membuat Treeview dengan scrollbar vertikal."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, sticky="nsew", padx=padx)
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(column, weight=1)
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=5)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for name, heading, width in zip(columns, headings, widths):
            tree.heading(name, text=heading)
            tree.column(name, width=width, minwidth=70, anchor="center")
        return tree

    def _add_item(self, kind):
        """Menambahkan satu nama unik dari form setup."""
        is_criteria = kind == "criteria"
        entry = self.criteria_input if is_criteria else self.alternative_input
        items = self.criteria if is_criteria else self.alternatives
        name = entry.get().strip()
        if not name:
            messagebox.showwarning("Input kosong", "Nama tidak boleh kosong.")
            return
        if any(existing.casefold() == name.casefold() for existing in items):
            messagebox.showwarning("Nama duplikat", "Nama tersebut sudah terdaftar.")
            return

        items.append(name)
        entry.delete(0, tk.END)
        self._refresh_setup_lists()
        self._rebuild_matrices()

    def _remove_item(self, kind):
        """Menghapus item yang sedang dipilih dari salah satu daftar."""
        is_criteria = kind == "criteria"
        listbox = self.criteria_list if is_criteria else self.alternative_list
        items = self.criteria if is_criteria else self.alternatives
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Belum dipilih", "Pilih item yang ingin dihapus.")
            return
        del items[selection[0]]
        self._refresh_setup_lists()
        self._rebuild_matrices()

    def _reset_sample_data(self):
        """Mengembalikan kriteria, alternatif, dan matriks ke data contoh awal."""
        self.criteria = ["Harga", "Kualitas", "Garansi"]
        self.alternatives = ["Produk A", "Produk B", "Produk C"]
        self._refresh_setup_lists()
        self._rebuild_matrices()

    def _refresh_setup_lists(self):
        """Menyelaraskan tampilan Listbox dengan data aplikasi."""
        self.criteria_list.delete(0, tk.END)
        for item in self.criteria:
            self.criteria_list.insert(tk.END, item)
        self.alternative_list.delete(0, tk.END)
        for item in self.alternatives:
            self.alternative_list.insert(tk.END, item)

    def _rebuild_matrices(self):
        """Membangun matriks kriteria dan matriks alternatif per kriteria."""
        for tab_id in self.matrix_notebook.tabs():
            self.matrix_notebook.forget(tab_id)
        self.matrix_vars.clear()

        if self.criteria:
            self._add_matrix_tab(
                "criteria",
                "Perbandingan Kriteria",
                self.criteria,
            )
            if self.alternatives:
                for index, criterion in enumerate(self.criteria):
                    self._add_matrix_tab(
                        ("alternative", index),
                        f"Alternatif: {criterion}",
                        self.alternatives,
                    )
        else:
            empty = ttk.Frame(self.matrix_notebook, padding=20)
            ttk.Label(
                empty, text="Tambahkan kriteria pada tab Setup untuk membuat matriks."
            ).pack(anchor="w")
            self.matrix_notebook.add(empty, text="Belum ada matriks")

        # Matriks baru langsung mendapat data uji yang valid dan hasil dihitung.
        self._autofill_matrices(randomize=False, notify=False)

    def _add_matrix_tab(self, matrix_key, title, labels):
        """Membuat satu matriks n x n; diagonal utama dibuat terkunci."""
        frame = ttk.Frame(self.matrix_notebook, padding=10)
        self.matrix_notebook.add(frame, text=title[:28])
        canvas = tk.Canvas(frame, highlightthickness=0)
        vertical = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        table = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=table, anchor="nw")
        table.bind(
            "<Configure>",
            lambda _event, target=canvas: target.configure(
                scrollregion=target.bbox("all")
            ),
        )
        canvas.bind(
            "<Configure>",
            lambda event, target=canvas, window=canvas_window: target.itemconfigure(
                window, width=max(event.width, table.winfo_reqwidth())
            ),
        )

        ttk.Label(table, text="Kriteria / Alternatif", style="Heading.TLabel").grid(
            row=0, column=0, sticky="nsew", padx=3, pady=3
        )
        for column, label in enumerate(labels, start=1):
            ttk.Label(
                table,
                text=label,
                style="Heading.TLabel",
                width=12,
                anchor="center",
            ).grid(row=0, column=column, sticky="nsew", padx=3, pady=3)
        for row, label in enumerate(labels, start=1):
            ttk.Label(
                table,
                text=label,
                style="Heading.TLabel",
                width=22,
                anchor="w",
            ).grid(row=row, column=0, sticky="nsew", padx=3, pady=3)

        variables = []
        for row in range(len(labels)):
            row_vars = []
            for column in range(len(labels)):
                value = tk.StringVar(value="1" if row == column else "")
                row_vars.append(value)
                entry = ttk.Entry(
                    table,
                    textvariable=value,
                    width=10,
                    justify="center",
                    state="readonly" if row == column else "normal",
                )
                if row != column:
                    value.trace_add(
                        "write",
                        lambda *_args, key=matrix_key, r=row, c=column:
                        self._matrix_value_changed(key, r, c),
                    )
                entry.grid(
                    row=row + 1,
                    column=column + 1,
                    sticky="nsew",
                    padx=3,
                    pady=3,
                )
            variables.append(row_vars)
        self.matrix_vars[matrix_key] = variables

    def _autofill_matrices(self, randomize=True, notify=True):
        """Mengisi matriks dengan nilai Saaty acak atau data contoh deterministik."""
        if not self.matrix_vars:
            if notify:
                messagebox.showwarning(
                    "Matriks belum tersedia", "Tambahkan kriteria terlebih dahulu."
                )
            else:
                self._calculate(show_errors=False)
            return
        sample_values = (
            3.0,
            5.0,
            1.0 / 3.0,
            2.0,
            1.0 / 5.0,
            1.0 / 2.0,
            4.0,
            1.0 / 4.0,
        )
        self._suspend_matrix_updates = True
        try:
            for matrix_index, variables in enumerate(self.matrix_vars.values()):
                size = len(variables)
                for row in range(size):
                    variables[row][row].set("1")
                    for column in range(row + 1, size):
                        if randomize:
                            value = random.choice(SAATY_VALUES)
                        else:
                            value_index = (
                                row * size + column + matrix_index
                            ) % len(sample_values)
                            value = sample_values[value_index]
                        variables[row][column].set(self._format_value(value))
                        variables[column][row].set(self._format_value(1.0 / value))
        finally:
            self._suspend_matrix_updates = False
        self._calculate(show_errors=False)
        if notify:
            messagebox.showinfo(
                "Selesai", "Semua matriks terisi dengan nilai Saaty yang resiprokal."
            )

    def _matrix_value_changed(self, matrix_key, row, column):
        """Menjaga pasangan resiprokal dan menjadwalkan hitung ulang otomatis."""
        if self._suspend_matrix_updates:
            return
        variables = self.matrix_vars[matrix_key]
        current = variables[row][column].get().strip()
        try:
            value = self._parse_saaty_value(
                current, "Matriks", str(row + 1), str(column + 1)
            )
        except ValueError:
            self._schedule_calculation()
            return

        self._suspend_matrix_updates = True
        try:
            variables[column][row].set(self._format_value(1.0 / value))
        finally:
            self._suspend_matrix_updates = False
        self._schedule_calculation()

    def _schedule_calculation(self):
        """Menggabungkan perubahan input cepat menjadi satu kalkulasi saat idle."""
        if not self._calculation_pending:
            self._calculation_pending = True
            self.root.after_idle(self._run_scheduled_calculation)

    def _run_scheduled_calculation(self):
        """Callback Tkinter untuk memperbarui hasil setelah input berubah."""
        self._calculation_pending = False
        self._calculate(show_errors=False)

    @staticmethod
    def _format_value(value):
        """Menyajikan bilangan bulat atau resiprokalnya dengan format ringkas."""
        rounded = round(value)
        if abs(value - rounded) < 1e-10:
            return str(int(rounded))
        reciprocal = 1.0 / value
        reciprocal_rounded = round(reciprocal)
        if abs(reciprocal - reciprocal_rounded) < 1e-10:
            return f"1/{int(reciprocal_rounded)}"
        return f"{value:.6g}"

    @staticmethod
    def _parse_saaty_value(text, matrix_name, row, column):
        """Memvalidasi input agar hanya berisi skala Saaty dan kebalikannya."""
        try:
            value = float(Fraction(text.strip()))
        except (ValueError, ZeroDivisionError):
            raise ValueError(
                f"Nilai pada {matrix_name} ({row}, {column}) tidak valid: {text!r}."
            ) from None
        if not np.isfinite(value) or value <= 0:
            raise ValueError(
                f"Nilai pada {matrix_name} ({row}, {column}) harus positif."
            )
        if not any(np.isclose(value, valid, rtol=1e-7, atol=1e-9) for valid in SAATY_VALUES):
            raise ValueError(
                f"Nilai {text!r} pada {matrix_name} ({row}, {column}) "
                "bukan skala Saaty yang valid (1–9 atau kebalikannya)."
            )
        return value

    def _read_matrix(self, matrix_key, labels, matrix_name):
        """Membaca matriks input dan memeriksa diagonal serta sifat resiprokal."""
        variables = self.matrix_vars[matrix_key]
        size = len(labels)
        matrix = np.zeros((size, size), dtype=float)
        for row in range(size):
            for column in range(size):
                matrix[row, column] = self._parse_saaty_value(
                    variables[row][column].get(),
                    matrix_name,
                    labels[row],
                    labels[column],
                )
                if row == column and not np.isclose(matrix[row, column], 1.0):
                    raise ValueError(f"Diagonal matriks {matrix_name} harus bernilai 1.")
        if not np.allclose(matrix * matrix.T, 1.0, rtol=1e-6, atol=1e-6):
            raise ValueError(
                f"Matriks {matrix_name} harus resiprokal. "
                "Jika A terhadap B bernilai 3, B terhadap A harus 1/3."
            )
        return matrix

    @staticmethod
    def _calculate_priority(matrix):
        """Menghasilkan matriks normalisasi, eigenvector utama, dan konsistensi."""
        size = matrix.shape[0]
        column_totals = matrix.sum(axis=0)
        normalized = matrix / column_totals

        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        principal_index = int(np.argmax(eigenvalues.real))
        lambda_max = float(eigenvalues[principal_index].real)
        priority = np.abs(eigenvectors[:, principal_index].real)
        priority = priority / priority.sum()

        consistency_index = (
            (lambda_max - size) / (size - 1) if size > 1 else 0.0
        )
        random_index = RANDOM_INDEX.get(size)
        if random_index is None:
            raise ValueError(
                f"Ukuran matriks {size} belum didukung tabel RI. "
                "Gunakan maksimal 15 item per matriks."
            )
        consistency_ratio = (
            consistency_index / random_index if random_index else 0.0
        )
        return normalized, priority, lambda_max, consistency_index, consistency_ratio

    def _calculate(self, show_errors=True):
        """Memvalidasi input, menghitung bobot global, dan menampilkan hasil."""
        if not self.criteria:
            self._calculation_error("Tambahkan minimal satu kriteria.", show_errors)
            return
        if not self.alternatives:
            self._calculation_error("Tambahkan minimal satu alternatif.", show_errors)
            return
        if len(self.criteria) > 15 or len(self.alternatives) > 15:
            self._calculation_error(
                "Tabel Random Index mendukung maksimal 15 item per matriks.",
                show_errors,
            )
            return

        try:
            criteria_matrix = self._read_matrix(
                "criteria", self.criteria, "Perbandingan Kriteria"
            )
            (
                criteria_normalized,
                criteria_weights,
                *criteria_test,
            ) = self._calculate_priority(criteria_matrix)

            alternative_weights = []
            alternative_tests = []
            alternative_normalized = []
            for index, criterion in enumerate(self.criteria):
                matrix = self._read_matrix(
                    ("alternative", index),
                    self.alternatives,
                    f"Alternatif untuk {criterion}",
                )
                normalized, weights, *test = self._calculate_priority(matrix)
                alternative_normalized.append(normalized)
                alternative_weights.append(weights)
                alternative_tests.append(test)
        except ValueError as error:
            self._calculation_error(str(error), show_errors)
            return

        global_scores = np.asarray(criteria_weights) @ np.asarray(alternative_weights)
        order = np.argsort(global_scores)[::-1]

        self._clear_tree(self.ranking_table)
        for rank, index in enumerate(order, start=1):
            self.ranking_table.insert(
                "",
                tk.END,
                values=(
                    rank,
                    self.alternatives[index],
                    f"{global_scores[index]:.6f}",
                ),
            )

        self._clear_tree(self.criteria_weights_table)
        for criterion, weight in zip(self.criteria, criteria_weights):
            self.criteria_weights_table.insert(
                "", tk.END, values=(criterion, f"{weight:.6f}")
            )

        self._clear_tree(self.consistency_table)
        all_tests = [("Perbandingan Kriteria", criteria_test)]
        all_tests.extend(
            (f"Alternatif - {criterion}", test)
            for criterion, test in zip(self.criteria, alternative_tests)
        )
        for matrix_name, test in all_tests:
            lambda_max, consistency_index, consistency_ratio = test
            status = "Konsisten" if consistency_ratio <= 0.1 else "Tidak konsisten"
            self.consistency_table.insert(
                "",
                tk.END,
                values=(
                    matrix_name,
                    f"{lambda_max:.4f}",
                    f"{consistency_index:.4f}",
                    f"{consistency_ratio:.4f}",
                    status,
                ),
            )

        # Tampilkan matriks normalisasi agar langkah perhitungan dapat diperiksa.
        for tab_id in self.detail_notebook.tabs()[1:]:
            self.detail_notebook.forget(tab_id)
        self._add_normalized_matrix(
            "Normalisasi Kriteria", self.criteria, criteria_normalized
        )
        self._add_local_priority_table(alternative_weights)
        for criterion, normalized in zip(self.criteria, alternative_normalized):
            self._add_normalized_matrix(
                f"Normalisasi: {criterion}", self.alternatives, normalized
            )
        self.result_status.configure(
            text=(
                "Hasil diperbarui otomatis: bobot eigenvector, normalisasi, "
                "uji konsistensi, dan peringkat."
            )
        )

    def _add_local_priority_table(self, alternative_weights):
        """Menampilkan eigenvector lokal alternatif untuk setiap kriteria."""
        frame = ttk.Frame(self.detail_notebook, padding=8)
        self.detail_notebook.add(frame, text="Eigenvector Alternatif")
        columns = ("alternative",) + tuple(
            f"criterion_{index}" for index in range(len(self.criteria))
        )
        headings = ("Alternatif",) + tuple(self.criteria)
        widths = (200,) + (120,) * len(self.criteria)
        table = self._create_tree(
            frame,
            columns=columns,
            headings=headings,
            widths=widths,
            row=0,
            column=0,
        )
        for alternative_index, alternative in enumerate(self.alternatives):
            values = tuple(
                f"{weights[alternative_index]:.6f}"
                for weights in alternative_weights
            )
            table.insert("", tk.END, values=(alternative,) + values)

    def _calculation_error(self, message, show_dialog):
        """Menjelaskan kegagalan input dan mencegah hasil lama tampak berlaku."""
        self.result_status.configure(text=f"Perhitungan belum tersedia: {message}")
        self._clear_tree(self.ranking_table)
        self._clear_tree(self.criteria_weights_table)
        self._clear_tree(self.consistency_table)
        for tab_id in self.detail_notebook.tabs()[1:]:
            self.detail_notebook.forget(tab_id)
        if show_dialog:
            messagebox.showerror("Perhitungan AHP belum dapat dilakukan", message)

    def _add_normalized_matrix(self, title, labels, normalized):
        """Menampilkan hasil normalisasi satu matriks pada tab detail."""
        frame = ttk.Frame(self.detail_notebook, padding=8)
        self.detail_notebook.add(frame, text=title[:28])
        columns = ("item",) + tuple(f"column_{index}" for index in range(len(labels)))
        headings = ("Kriteria / Alternatif",) + tuple(labels)
        widths = (200,) + (110,) * len(labels)
        table = self._create_tree(
            frame,
            columns=columns,
            headings=headings,
            widths=widths,
            row=0,
            column=0,
        )
        for label, row_values in zip(labels, normalized):
            table.insert(
                "",
                tk.END,
                values=(label,) + tuple(f"{value:.4f}" for value in row_values),
            )

    @staticmethod
    def _clear_tree(tree):
        """Menghapus baris hasil sebelumnya dari Treeview."""
        for item in tree.get_children():
            tree.delete(item)


def main():
    """Titik masuk program desktop."""
    root = tk.Tk()
    AHPApplication(root)
    root.mainloop()


if __name__ == "__main__":
    main()