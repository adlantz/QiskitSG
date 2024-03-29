import numpy as np
import random
import tfim
import itertools as it
import argparse

import threading
import sys, os
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize, QPointF
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QColor
from PyQt5.QtWidgets import QApplication


def main():
    App = QApplication(sys.argv)
    window = Window()
    sys.exit(App.exec())


class Window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        parser = argparse.ArgumentParser(
            description=("Visualization of infinite dimensional Ising model spin glass")
        )
        parser.add_argument("-N", type=int, default=4, help="Number of spins")
        parser.add_argument(
            "-loadBC", action="store_true", help="Load bond configuration"
        )
        parser.add_argument(
            "-BC", type=str, default="101011", help="Bond Configuration"
        )
        args = parser.parse_args()

        # Set these to True to see bipartitions or Energy info, respectively
        ######################################################################
        self.show_bps = False
        self.show_Ens = True
        ######################################################################

        # Window size and label
        self.title = "SGViz_InfD"
        self.top = 50
        self.left = 100
        self.width = 1000
        self.height = 750

        self.loadBC = args.loadBC
        self.BC = args.BC

        (self.Swidth, self.Sheight) = scaleDims(self.width, self.height)

        # Set initial parameters
        self.N = args.N
        self.seed = 0
        self.G = tfim.Jij_instance(self.N, 1, "bimodal", self.seed, True)
        if self.loadBC:
            self.Jij = BCtoJij(args.N, str(self.BC))
            self.G = JijtoG(self.Jij, self.N)
        else:
            self.Jij = makeJij(self.G, self.N)

        if self.show_Ens:
            self.lattice = tfim.Lattice([self.N])
            self.basis = tfim.IsingBasis(self.lattice)
            self.JZZ = tfim.JZZ_SK(self.basis, self.G)
            self.ea = -(self.JZZ.diagonal())
            self.gs = np.where(self.ea == self.ea.min())[0]

        self.cnfg = self.gs[0]
        self.configuration = list(map(int, list(bin(self.cnfg)[2:].zfill(self.N))))
        self.center = (500, 375)
        self.coordList = spinCoords(self.N, self.center, 290)
        combos = list(it.combinations([i for i in range(int(self.N))], int(self.N / 2)))
        self.permlist = []
        for i in range(int(len(combos) / 2)):
            self.permlist.append(combos[i] + combos[int(len(combos)) - 1 - i])
        self.pi = 0
        self.p = self.permlist[self.pi]

        self.clear = False

        self.setStyleSheet("background-color: white;")

        self.Ealabel = QLabel(self)
        self.Enlabel = QLabel(self)
        self.Clabel = QLabel(self)
        self.cEdit = QLineEdit(self)
        self.cLabel = QLabel(self)
        self.countLabel = QLabel(self)
        self.scountLabel = QLabel(self)
        # self.sEdit = QLineEdit(self)
        # self.sLabel = QLabel(self)
        # self.pEdit = QLineEdit(self)
        # self.pLabel = QLabel(self)
        # self.NEdit = QLineEdit(self)
        self.NLabel = QLabel(self)
        self.pybutton = QPushButton("Enter", self)
        self.pybutton.setStyleSheet(
            "QPushButton {color: white; background-color: black}"
        )
        self.pybutton.clicked.connect(self.clickMethod)
        self.Cpybutton = QPushButton("Clear", self)
        self.Cpybutton.setStyleSheet(
            "QPushButton {color: white; background-color: black}"
        )
        self.Cpybutton.clicked.connect(self.clearMethod)
        self.Resizebutton = QPushButton("Resize", self)
        self.Resizebutton.setStyleSheet(
            "QPushButton {color: white; background-color: black}"
        )
        self.Resizebutton.clicked.connect(self.resizeMethod)
        self.BCLabel = QLabel(self)
        self.CLLabel = QLabel(self)

        self.editLabels()

        self.InitWindow()

    def keyPressEvent(self, qKeyEvent):
        if qKeyEvent.key() == QtCore.Qt.Key_Return:
            self.clickMethod()

    def InitWindow(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()

    def clickMethod(self):
        thread = threading.Thread(target=self.DynMethod())
        thread.start()

    def resizeMethod(self):
        self.width = self.size().width()
        self.height = self.size().height()
        (self.Swidth, self.Sheight) = scaleDims(self.width, self.height)
        self.editLabels()
        self.repaint()

    def clearMethod(self):
        if not self.clear:
            self.clear = True
            self.Sheight += 99999
            self.editLabels()
            self.Sheight -= 99999
        else:
            self.clear = False
            self.editLabels()

    def DynMethod(self):
        change = False

        # ns = self.NEdit.text()
        # if len(ns) > 0:
        # 	change = True
        # 	n = int(ns)
        # 	if n != self.N:
        # 		self.N = n
        # 		self.coordList = spinCoords(self.N, (500,375),300)
        # 		lattice = tfim.Lattice([self.N])
        # 		basis = tfim.IsingBasis(lattice)
        # 		combos = list(it.combinations([i for i in range(int(self.N))],int(self.N / 2)))
        # 		self.permlist = []
        # 		for i in range(int(len(combos)/2)):
        # 			self.permlist.append(combos[i] + combos[int(len(combos))-1-i])
        # 		self.pi = 0
        # 		self.p = self.permlist[self.pi]

        # ss = self.sEdit.text()
        # if len(ss) > 0:
        # 	change = True
        # 	s = int(ss)
        # 	if s != self.seed:
        # 		self.seed = s
        # 		ss = self.sEdit.text()

        cs = self.cEdit.text()
        if len(cs) > 0:
            change = True
            c = int(cs)
            if c != self.cnfg:
                self.cnfg = c

        if change:
            self.G = tfim.Jij_instance(self.N, 1, "bimodal", self.seed, True)
            if self.loadBC:
                self.Jij = BCtoJij(self.N, str(self.BC))
                self.G = JijtoG(self.Jij, self.N)
            else:
                self.Jij = makeJij(self.G, self.N)
            self.configuration = list(map(int, list(bin(self.cnfg)[2:].zfill(self.N))))
            self.Clabel.setText("Current State: " + str(self.configuration))

            if self.show_Ens:
                self.lattice = tfim.Lattice([self.N])
                self.basis = tfim.IsingBasis(self.lattice)
                self.JZZ = tfim.JZZ_SK(self.basis, self.G)
                self.ea = -(self.JZZ.diagonal())
                self.gs = np.where(self.ea == self.ea.min())[0]
                self.Ealabel.setText("Ground States: " + str(self.gs))
                self.Enlabel.setText("Current Energy: " + str(self.ea[self.cnfg]))

        # ps = self.pEdit.text()
        # if len(ps) > 0:
        # 	bp = int(ps)
        # 	if bp != self.pi:
        # 		self.pi = bp
        # 		self.p = self.permlist[self.pi]

        self.repaint()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.scale(self.Swidth / 1000, self.Swidth / 1000)
        qp.setPen(QPen(Qt.blue, 3))
        self.drawBonds(qp, self.coordList, self.configuration)
        self.drawSpins(qp, self.coordList)
        self.labelSpins(qp, self.coordList)
        self.drawConfiguration(qp, self.configuration, self.coordList)
        qp.end()

    def drawSpins(self, qp, coordList):
        qp.setBrush(QBrush(QColor(0, 0, 0), Qt.SolidPattern))
        for i in range(len(coordList) - 1, -1, -1):
            qp.setPen(QPen(spinColor(self.p, i, self.show_bps), 5))

            c = coordList[i]
            qp.drawEllipse(c - QPointF(25, 25), 50, 50)
            # qp.drawEllipse(c[0] - 25, c[1] - 25, 50, 50)

    def drawBonds(self, qp, coordList, config):
        self.ubondCountArray = [0 for i in range(self.N)]
        self.sbondCountArray = [0 for i in range(self.N)]
        for i in range(self.N):
            for j in range(i + 1, self.N):
                if (
                    int(self.Jij[i][j] * (2 * config[i] - 1) * (2 * config[j] - 1))
                    == -1
                ):
                    self.ubondCountArray[i] += 1
                    self.ubondCountArray[j] += 1
                    qp.setPen(QPen(bondColor(self.Jij, i, j), 5, Qt.DashLine))
                else:
                    self.sbondCountArray[i] += 1
                    self.sbondCountArray[j] += 1
                    qp.setPen(QPen(bondColor(self.Jij, i, j), 5, Qt.SolidLine))
                ci = coordList[i]
                cj = coordList[j]
                qp.drawLine(ci, cj)
        self.countLabel.setText("Unsatisfied: " + str(sum(self.ubondCountArray) // 2))
        self.scountLabel.setText("Satisfied: " + str(sum(self.sbondCountArray) // 2))

    def labelSpins(self, qp, coordList):
        qp.setPen(Qt.black)

        i = 0
        for c in coordList:
            angle = (2 * i * (np.pi)) / self.N
            qp.setFont(QFont("Arial", 15))
            # uncomment following line for labels
            qp.drawText(
                int(self.center[0] - 5 - 350 * np.cos(angle)),
                int(self.center[1] + 5 - 350 * np.sin(angle)),
                str(i),
            )

            i += 1

    def drawConfiguration(self, qp, config, coordList):
        i = 0
        for c in coordList:
            if config[i] == 1:
                qp.setPen(QPen(Qt.magenta, 4))
                self.drawArrow(qp, 1, c)
            else:
                qp.setPen(QPen(Qt.cyan, 4))
                self.drawArrow(qp, -1, c)
            i += 1

    def drawArrow(self, qp, dir, coords):
        qp.drawLine(coords + QPointF(0, dir * 15), coords - QPointF(0, dir * 15))
        qp.drawLine(coords - QPointF(10, dir * 5), coords - QPointF(0, dir * 15))
        qp.drawLine(coords + QPointF(10, -(dir * 5)), coords - QPointF(0, dir * 15))
        # qp.drawLine(
        #     coords[0], coords[1] + (dir * 15), coords[0], coords[1] - (dir * 15)
        # )
        # qp.drawLine(
        #     coords[0] - 10, coords[1] - (dir * 5), coords[0], coords[1] - (dir * 15)
        # )
        # qp.drawLine(
        #     coords[0] + 10, coords[1] - (dir * 5), coords[0], coords[1] - (dir * 15)
        # )

    def editLabels(self):
        fontsize = int((self.Swidth / 1000) * 13)

        if self.show_Ens:
            self.Ealabel.setFont(QFont("Arial", fontsize))
            self.Ealabel.setStyleSheet("color: black")
            self.Ealabel.resize(int(0.3 * self.Swidth), int(0.04 * self.Sheight))
            self.Ealabel.move(int(0.02 * self.Swidth), int(0.067 * self.Sheight))
            self.Ealabel.setText("Ground States: " + str(self.gs))

            self.Enlabel.setFont(QFont("Arial", fontsize))
            self.Enlabel.setStyleSheet("color: black")
            self.Enlabel.resize(int(0.2 * self.Swidth), int(0.04 * self.Sheight))
            self.Enlabel.move(int(0.02 * self.Swidth), int(0.107 * self.Sheight))
            self.Enlabel.setText("Current Energy: " + str(self.ea[self.cnfg]))

        self.Clabel.setFont(QFont("Arial", fontsize))
        self.Clabel.setStyleSheet("color: black")
        self.Clabel.resize(int(0.4 * self.Swidth), int(0.04 * self.Sheight))
        self.Clabel.move(int(0.7 * self.Swidth), int(0.023 * self.Sheight))
        self.Clabel.setText("Current State: " + str(self.configuration))

        self.cEdit.setStyleSheet("color: black")
        self.cEdit.move(int(0.08 * self.Swidth), int(0.933 * self.Sheight))
        self.cEdit.resize(int(0.1 * self.Swidth), int(0.043 * self.Sheight))

        self.cLabel.setStyleSheet("color: black")
        self.cLabel.setFont(QFont("Arial", fontsize))
        self.cLabel.setText("State: ")
        self.cLabel.move(int(0.02 * self.Swidth), int(0.93 * self.Sheight))
        self.cLabel.resize(int(0.05 * self.Swidth), int(0.043 * self.Sheight))

        self.countLabel.setStyleSheet("color: black")
        self.countLabel.setFont(QFont("Arial", fontsize))
        self.countLabel.setText("unsatisfied: ")
        self.countLabel.move(int(0.02 * self.Swidth), int(0.267 * self.Sheight))
        self.countLabel.resize(int(0.1 * self.Swidth), int(0.043 * self.Sheight))

        self.scountLabel.setStyleSheet("color: black")
        self.scountLabel.setFont(QFont("Arial", fontsize))
        self.scountLabel.setText("satisfied: ")
        self.scountLabel.move(int(0.02 * self.Swidth), int(0.333 * self.Sheight))
        self.scountLabel.resize(int(0.1 * self.Swidth), int(0.043 * self.Sheight))

        # self.sEdit.setStyleSheet("color: black")
        # self.sEdit.move(0.08*self.Swidth, 0.867*self.Sheight)
        # self.sEdit.resize(int(0.1*self.Swidth),int(0.043*self.Sheight))

        # self.sLabel.setStyleSheet("color: black")
        # self.sLabel.setFont(QFont('Arial', fontsize))
        # self.sLabel.setText("Seed")
        # self.sLabel.move(0.02*self.Swidth,0.867*self.Sheight)
        # self.sLabel.resize(int(0.05*self.Swidth),int(0.043*self.Sheight))

        # self.pEdit.setStyleSheet("color: black")
        # self.pEdit.move(0.85*self.Swidth, 0.867*self.Sheight)
        # self.pEdit.resize(int(0.1*self.Swidth),int(0.043*self.Sheight))

        # self.pLabel.setStyleSheet("color: black")
        # self.pLabel.setFont(QFont('Arial', fontsize))
        # self.pLabel.setText("Bipartition")
        # self.pLabel.move(0.74*self.Swidth,0.867*self.Sheight)
        # self.pLabel.resize(int(0.075*self.Swidth),int(0.043*self.Sheight))

        # self.NEdit.setStyleSheet("color: black")
        # self.NEdit.move(0.08*self.Swidth, 0.8*self.Sheight)
        # self.NEdit.resize(int(0.1*self.Swidth),int(0.043*self.Sheight))

        self.NLabel.setStyleSheet("color: black")
        self.NLabel.setFont(QFont("Arial", fontsize))
        self.NLabel.setText("N: " + str(self.N))
        self.NLabel.move(int(0.02 * self.Swidth), int(0.8 * self.Sheight))
        self.NLabel.resize(int(0.05 * self.Swidth), int(0.043 * self.Sheight))

        self.BCLabel.setStyleSheet("color: black")
        self.BCLabel.setFont(QFont("Arial", fontsize))
        self.BCLabel.setText("Bond Configuration: " + str(self.BC)[::-1])
        self.BCLabel.move(int(0.7 * self.Swidth), int(0.1 * self.Sheight))
        self.BCLabel.resize(int(0.3 * self.Swidth), int(0.043 * self.Sheight))

        self.CLLabel.setStyleSheet("color: black")
        self.CLLabel.setFont(QFont("Arial", fontsize))
        self.CLLabel.setText(
            "Bond List:\n"
            + str(
                np.array(
                    [
                        np.array(list(c))
                        for c in it.combinations([i for i in range(self.N)], 2)
                    ]
                )
            )
        )
        self.CLLabel.move(int(0.9 * self.Swidth), int(0.15 * self.Sheight))
        self.CLLabel.resize(int(0.3 * self.Swidth), int(1 * self.Sheight))

        self.pybutton.resize(int(0.1 * self.Swidth), int(0.043 * self.Sheight))
        self.pybutton.move(int(0.3 * self.Swidth), int(0.933 * self.Sheight))

        if not self.clear:
            self.Cpybutton.resize(int(0.1 * self.Swidth), int(0.043 * self.Sheight))
            self.Cpybutton.move(int(0.01 * self.Swidth), int(0.013 * self.Sheight))

        self.Resizebutton.resize(int(0.1 * self.Swidth), int(0.043 * self.Sheight))
        self.Resizebutton.move(int(0.12 * self.Swidth), int(0.013 * self.Sheight))


def scaleDims(width, height):
    if height / width > 00.75:
        Swidth = width
        Sheight = width * 0.75
    elif height / width < 00.75:
        Swidth = height / 0.75
        Sheight = height
    else:
        Swidth = width
        Sheight = height

    return (Swidth, Sheight)


def spinCoords(N, center, r):
    coords = []
    for i in range(N):
        angle = (2 * i * (np.pi)) / N
        c = QPointF(
            float(center[0] - r * np.cos(angle)), float(center[1] - r * np.sin(angle))
        )
        # x = QPointF(center[0] - r * np.cos(angle))
        # y = QPointF(center[1] - r * np.sin(angle))
        # c = (x, y)
        coords.append(c)
    return coords


def makeJij(G, N):
    """
    Turns Jij matrix from form built in tfim.py to standard Jij where J[i][j] is the bond between spins i and j
    """
    Jij = np.zeros((N, N))
    for j in range(N // 2):
        for i in range(N):
            Jij[i][(i - j + N - 1) % N] = Jij[(i - j + N - 1) % N][i] = G[j][i]
    return Jij


def BCtoJij(N, BC):
    clause_list = np.array(
        [np.array(list(c)) for c in it.combinations([i for i in range(N)], 2)]
    )
    BCA = [int(i) for i in BC]
    BCA.reverse()
    Jij = np.zeros((N, N))
    i = 0
    for clause in clause_list:
        Jij[clause[0]][clause[1]] = -1 + 2 * BCA[i]
        Jij[clause[1]][clause[0]] = -1 + 2 * BCA[i]
        i += 1
    return Jij


def JijtoG(Jij, N):
    G = np.empty((N // 2, N))
    for j in range(N // 2):
        for i in range(N):
            G[j][i] = Jij[i][(i - j + N - 1) % N]
    return G


def bondColor(Jij, i, j):
    if Jij[i][j] == 1:
        return Qt.red
    else:
        return Qt.blue


# BIPARTITION COLOR


def spinColor(p, i, show_bps):
    if show_bps:
        A = p[0 : len(p) // 2]
        if i in A:
            return Qt.yellow
        else:
            return Qt.green
    else:
        return Qt.black


if __name__ == "__main__":
    main()
