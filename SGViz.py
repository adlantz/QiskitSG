"""Visualization of an infinite-dimensional Ising model spin glass."""

import argparse
import itertools as it
import sys

import numpy as np
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import tfim

# Set to True to color spins by bipartition
SHOW_BIPARTITION = False

SEED = 0
# Logical canvas size; everything is laid out in these units and scaled to the window
BASE_WIDTH = 1060
BASE_HEIGHT = 750
MARGIN = 16
PANEL_WIDTH = 280
CENTER = (680, 375)
SPIN_RADIUS = 290
LABEL_RADIUS = 350
UI_FONTS = ["Helvetica Neue", "Segoe UI", "Arial"]


class Window(QMainWindow):
    def __init__(self, n, bond_config, load_bc):
        super().__init__()
        self.n = n
        self.bonds = list(it.combinations(range(n), 2))
        self.scale = 1.0

        if load_bc:
            self.jij = bond_config_to_jij(n, bond_config)
            g = jij_to_g(self.jij)
        else:
            g = tfim.Jij_instance(n, 1, "bimodal", SEED, True)
            self.jij = g_to_jij(g)

        basis = tfim.IsingBasis(tfim.Lattice([n]))
        self.energies = -tfim.JZZ_SK(basis, g).diagonal()
        ground_states = np.flatnonzero(self.energies == self.energies.min())

        angles = 2 * np.pi * np.arange(n) / n
        self.spin_coords = [
            QPointF(CENTER[0] - SPIN_RADIUS * np.cos(a), CENTER[1] - SPIN_RADIUS * np.sin(a))
            for a in angles
        ]
        self.label_coords = [
            (
                int(CENTER[0] - 5 - LABEL_RADIUS * np.cos(a)),
                int(CENTER[1] + 5 - LABEL_RADIUS * np.sin(a)),
            )
            for a in angles
        ]

        available = set(QFontDatabase().families())
        self.ui_font = next((f for f in UI_FONTS if f in available), self.font().family())
        self.mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont).family()

        self.state_value = self._label(mono=True)
        self.energy_value = self._label()
        self.sat_value = self._label()
        self.unsat_value = self._label()
        self.state_edit = QLineEdit()
        self.state_edit.setPlaceholderText(f"0 – {2**n - 1}")
        self.toggle_button = QPushButton("Hide")
        self.toggle_button.clicked.connect(self.toggle_panel)
        enter_button = QPushButton("Enter")
        enter_button.clicked.connect(self.submit_state)

        self.content = QWidget()
        content = QVBoxLayout(self.content)
        content.setContentsMargins(0, 0, 0, 0)
        self.grid = QGridLayout()
        self.grid.setColumnStretch(1, 1)
        content.addLayout(self.grid)
        self._add_section("System", [
            ("Spins", self._label(str(n))),
            ("Bond config", self._label(group_bits(bond_config[::-1]), mono=True)),
        ])
        self._add_section("Current state", [
            ("Configuration", self.state_value),
            ("Energy", self.energy_value),
            ("Ground states", self._label(", ".join(map(str, ground_states)))),
        ])
        self._add_section("Bonds", [
            ("Satisfied", self.sat_value),
            ("Unsatisfied", self.unsat_value),
        ])
        self._add_section("Legend", [
            (swatch("━━━", "red"), self._label("J = +1")),
            (swatch("━━━", "blue"), self._label("J = −1")),
            (swatch("╌╌╌", "#555"), self._label("Unsatisfied bond")),
            (swatch("↑", "magenta") + " " + swatch("↓", "darkcyan"), self._label("Spin 1 / 0")),
        ])
        content.addStretch()
        content.addWidget(self._label("GO TO STATE", "header"))
        state_row = QHBoxLayout()
        state_row.addWidget(self.state_edit)
        state_row.addWidget(enter_button)
        content.addLayout(state_row)

        self.panel = QFrame(self)
        self.panel.setObjectName("panel")
        panel_layout = QVBoxLayout(self.panel)
        title_row = QHBoxLayout()
        title_row.addWidget(self._label("Spin Glass", "title"))
        title_row.addStretch()
        title_row.addWidget(self.toggle_button)
        panel_layout.addLayout(title_row)
        panel_layout.addWidget(self.content)

        self.setWindowTitle("SGViz_InfD")
        self.set_state(int(ground_states[0]))
        self.setGeometry(100, 50, BASE_WIDTH, BASE_HEIGHT)

    def _label(self, text="", name=None, mono=False):
        label = QLabel(text)
        label.setWordWrap(True)
        if mono:
            name = "mono"
        if name:
            label.setObjectName(name)
        return label

    def _add_section(self, title, rows):
        """Add a header plus key/value rows to the shared grid so columns line up."""
        row = self.grid.rowCount()
        self.grid.addWidget(self._label(title.upper(), "header"), row, 0, 1, 2)
        for i, (key, value) in enumerate(rows, start=row + 1):
            self.grid.addWidget(self._label(key, "key"), i, 0, Qt.AlignTop)
            self.grid.addWidget(value, i, 1)

    def _style(self, s):
        def px(v):
            return f"{max(1, round(v * s))}px"

        return f"""
            QWidget {{ font-family: "{self.ui_font}"; font-size: {px(14)}; color: #1d1d22; }}
            QMainWindow {{ background: white; }}
            QFrame#panel {{
                background: #f7f7f9;
                border: 1px solid #d4d4dc;
                border-radius: {px(10)};
            }}
            QLabel#title {{ font-size: {px(19)}; font-weight: 600; }}
            QLabel#header {{
                font-size: {px(11)};
                font-weight: 700;
                color: #85858f;
                padding-top: {px(12)};
            }}
            QLabel#key {{ color: #5b5b66; }}
            QLabel#mono {{ font-family: "{self.mono_font}"; }}
            QLineEdit {{
                background: white;
                border: 1px solid #c8c8d0;
                border-radius: {px(5)};
                padding: {px(4)} {px(6)};
            }}
            QPushButton {{
                background: #1d1d22;
                color: white;
                border: none;
                border-radius: {px(5)};
                padding: {px(5)} {px(12)};
            }}
            QPushButton:hover {{ background: #3a3a44; }}
        """

    def set_state(self, state):
        self.state = state
        self.spins = [int(b) for b in format(state, f"0{self.n}b")]
        sigma = [2 * s - 1 for s in self.spins]
        self.unsatisfied = {
            (i, j) for i, j in self.bonds if self.jij[i, j] * sigma[i] * sigma[j] < 0
        }

        self.state_value.setText(f"{''.join(map(str, self.spins))}  (#{state})")
        self.energy_value.setText(f"{self.energies[state]:g}")
        self.sat_value.setText(str(len(self.bonds) - len(self.unsatisfied)))
        self.unsat_value.setText(str(len(self.unsatisfied)))
        self.update()

    def submit_state(self):
        try:
            state = int(self.state_edit.text())
        except ValueError:
            return
        if 0 <= state < len(self.energies):
            self.set_state(state)

    def toggle_panel(self):
        self.content.setHidden(not self.content.isHidden())
        self.toggle_button.setText("Show" if self.content.isHidden() else "Hide")
        self._layout()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.submit_state()

    def resizeEvent(self, event):
        self._layout()
        super().resizeEvent(event)

    def _layout(self):
        s = self.scale = min(self.width() / BASE_WIDTH, self.height() / BASE_HEIGHT)
        self.setStyleSheet(self._style(s))
        margin = round(MARGIN * s)
        self.panel.layout().setContentsMargins(margin, margin, margin, margin)
        for layout in self.panel.findChildren(QLayout):
            layout.setSpacing(round(6 * s))

        if not self.content.isHidden():
            height = round((BASE_HEIGHT - 2 * MARGIN) * s)
        else:
            self.panel.layout().activate()
            height = self.panel.sizeHint().height()
        self.panel.setGeometry(margin, margin, round(PANEL_WIDTH * s), height)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.scale(self.scale, self.scale)
        self.draw_bonds(qp)
        self.draw_spins(qp)
        self.draw_spin_labels(qp)
        self.draw_arrows(qp)
        qp.end()

    def draw_bonds(self, qp):
        for i, j in self.bonds:
            style = Qt.DashLine if (i, j) in self.unsatisfied else Qt.SolidLine
            color = Qt.red if self.jij[i, j] == 1 else Qt.blue
            qp.setPen(QPen(color, 5, style))
            qp.drawLine(self.spin_coords[i], self.spin_coords[j])

    def draw_spins(self, qp):
        qp.setBrush(QColor(0, 0, 0))
        for i in reversed(range(self.n)):
            qp.setPen(QPen(spin_color(i, self.n), 5))
            qp.drawEllipse(self.spin_coords[i], 25, 25)

    def draw_spin_labels(self, qp):
        qp.setPen(Qt.black)
        qp.setFont(QFont(self.ui_font, 15))
        for i, (x, y) in enumerate(self.label_coords):
            qp.drawText(x, y, str(i))

    def draw_arrows(self, qp):
        for spin, c in zip(self.spins, self.spin_coords):
            qp.setPen(QPen(Qt.magenta if spin else Qt.cyan, 4))
            d = 1 if spin else -1
            tip = c - QPointF(0, 15 * d)
            qp.drawLine(c + QPointF(0, 15 * d), tip)
            qp.drawLine(c + QPointF(-10, -5 * d), tip)
            qp.drawLine(c + QPointF(10, -5 * d), tip)


def swatch(text, color):
    return f'<span style="color: {color}; font-weight: 700;">{text}</span>'


def group_bits(bits, size=4):
    """Split a bit string into space-separated groups so it can wrap."""
    return " ".join(bits[i : i + size] for i in range(0, len(bits), size))


def g_to_jij(g):
    """Convert the (N//2, N) coupling array from tfim.py to a symmetric Jij matrix."""
    n = g.shape[1]
    jij = np.zeros((n, n))
    i = np.arange(n)
    for j, row in enumerate(g):
        k = (i - j - 1) % n
        jij[i, k] = row
        jij[k, i] = row
    return jij


def jij_to_g(jij):
    """Inverse of g_to_jij."""
    n = len(jij)
    i = np.arange(n)
    return np.array([jij[i, (i - j - 1) % n] for j in range(n // 2)])


def bond_config_to_jij(n, bond_config):
    """Build Jij from a bit string with one bit per bond, last bit = bond (0, 1)."""
    jij = np.zeros((n, n))
    for (i, j), bit in zip(it.combinations(range(n), 2), reversed(bond_config)):
        jij[i, j] = jij[j, i] = 2 * int(bit) - 1
    return jij


def spin_color(i, n):
    if not SHOW_BIPARTITION:
        return Qt.black
    return Qt.yellow if i < n // 2 else Qt.green


def main():
    parser = argparse.ArgumentParser(
        description="Visualization of infinite dimensional Ising model spin glass"
    )
    parser.add_argument("-N", type=int, default=4, help="Number of spins")
    parser.add_argument("-loadBC", action="store_true", help="Load bond configuration")
    parser.add_argument("-BC", type=str, default="101011", help="Bond Configuration")
    args = parser.parse_args()

    num_bonds = args.N * (args.N - 1) // 2
    if args.loadBC and len(args.BC) != num_bonds:
        parser.error(f"-BC must have {num_bonds} bits for N={args.N}")

    app = QApplication(sys.argv)
    window = Window(args.N, args.BC, args.loadBC)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
