import sys
import random
from pyaudio import PyAudio
import numpy as np
import time
from PySide2 import QtWidgets, QtGui
from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox, QSizePolicy
from interface import Ui_MainWindow
from PySide2.QtCore import QFile, QObject, Signal, Slot, QTimer
from PySide2.QtWidgets import QApplication, QVBoxLayout, QWidget
from PySide2.QtUiTools import QUiLoader

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import threading

import time

DEBUG = False

class MatplotlibWidget(QWidget):

    fig = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.fig = Figure(figsize=(50, 50), dpi=65, facecolor=(1, 1, 1), edgecolor=(0, 0, 0), tight_layout=True)
        
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.setParent(parent)        

        lay = QVBoxLayout(self)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.canvas)

        self.ax = self.fig.add_subplot(111)
        self.line, *_ = self.ax.plot([])
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        #lay.setStretchFactor(self.canvas, 1)
        #FigureCanvas.resize(self, 900, 550)
        FigureCanvas.updateGeometry(self)

        self.ax.grid(True)
        self.ax.set_title("Sinal Reproduzido", fontsize=30)
        self.ax.set_xlabel("Tempo (s)", fontsize=20)
        self.ax.set_ylabel("Amplitude Relativa", fontsize=20)
        self.ax.autoscale(enable=True) 

        
    def resize_plot(self, size):
        #print(size)
        pixel_to_inch = 0.0154
        self.fig.set_size_inches(size.width()*pixel_to_inch*0.9, size.height()*pixel_to_inch*0.9, True)
        #self.canvas.updateGeometry()
        self.canvas.draw()
        #self.update()

    @Slot(list)
    def update_plot(self, x, y, freq):
        self.line.set_data(x, y)
        self.line.set_linewidth(3)

        self.ax.set_xlim(0, 1/freq*3)
        self.ax.set_ylim(min(y)*1.1, max(y)*1.1)
        
        tr = threading.Thread(target = self.canvas.draw, args = ())
        tr.start()
        



class MainWindow(QMainWindow):
    
    MPLWidget = None
    primeira = True
    resized = Signal()

    

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.pushButton.clicked.connect(self.play_sound)
        self.ui.pushButton_2.clicked.connect(self.stop_sound)
        self.resized.connect(self.resize_plot)
    
    


    def resizeEvent(self, event):
        self.resized.emit()
        return super(MainWindow, self).resizeEvent(event)

    def resize_plot(self):
        if self.MPLWidget is not None:
            self.MPLWidget.resize_plot(self.ui.groupBox.size())
    def resize_plot_delay(self, delay):
        time.sleep(delay)
        if self.MPLWidget is not None:
            self.MPLWidget.resize_plot(self.ui.groupBox.size())


    duracao = 0
    frequencias = [0, 0, 0]
    intensidades = [0, 0, 0]
    checkboxes = [False, False, False]
    tocando = False
    tocando2 = False
    tocando3 = False
    constante = False
    data = []
    data2 = []
    data3 = []

    def stop_sound(self):
        self.tocando = False
        self.tocando2 = False
        self.tocando3 = False

    def closeEvent(self, event):
        self.stop_sound()
        event.accept()

    def update_params(self):

        
        listaFrequencias = [self.ui.lineEdit, self.ui.lineEdit_4, self.ui.lineEdit_6]
        listaCheckboxes = [self.ui.checkBox, self.ui.checkBox_2, self.ui.checkBox_3]
        listaIntensidades = [self.ui.lineEdit_2, self.ui.lineEdit_3, self.ui.lineEdit_5]

        

        if DEBUG and self.primeira:
            listaFrequencias[0].setText("1000")
            listaFrequencias[1].setText("1100")
            listaIntensidades[0].setText("0")
            listaIntensidades[1].setText("0")
            self.ui.lineEdit_7.setText("1")
            listaCheckboxes[0].setChecked(True)
            listaCheckboxes[1].setChecked(True)
            self.primeira = False

        try:
            self.duracao = float(self.ui.lineEdit_7.text())
            if self.duracao < 0:
                raise ValueError('Valor menor que 0')
            
            self.constante = False

            if self.duracao == 0:
                self.duracao = 0.1
                self.constante = True

        except:
            self.ui.lineEdit_7.setText("")
            self.duracao = 0

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Entrada inválida.")
            msg.setInformativeText("A duração deve ser um número maior ou igual a 0.")
            msg.setWindowTitle("Erro na execução")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()

            return False  


        listaNomes = ["primeira", "segunda", "terceira"]

        allFalse = True

        for c in range(3):
            self.checkboxes[c] = False
            if listaCheckboxes[c].isChecked():
                allFalse = False
                self.checkboxes[c] = True

        if allFalse:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Entrada inválida.")
            msg.setInformativeText("Nenhuma componente habilitada.")
            msg.setWindowTitle("Erro na execução")
            msg.setStandardButtons(QMessageBox.Ok)
            retval = msg.exec_()

            return False

        for f in range(3):
            if listaCheckboxes[f].isChecked():
                try:
                    frequencia = float(listaFrequencias[f].text())
                    if frequencia < 0:
                        raise ValueError('Valor menor que 0')

                    self.frequencias[f] = frequencia
                    
                except:
                    listaFrequencias[f].setText("")
                    self.frequencias[f] = 0

                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Entrada inválida.")
                    msg.setInformativeText("A frequência da " + listaNomes[f] + " componente deve ser um número maior que 0.")
                    msg.setWindowTitle("Erro na execução")
                    msg.setStandardButtons(QMessageBox.Ok)
                    retval = msg.exec_()

                    return False
            
                try:
                    intensidade = float(listaIntensidades[f].text())
                    if intensidade > 0:
                        raise ValueError('Valor maior que 0')

                    self.intensidades[f] = intensidade
                    
                except:
                    listaIntensidades[f].setText("")
                    self.intensidades[f] = 0

                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Entrada inválida.")
                    msg.setInformativeText("A intensidade da " + listaNomes[f] + " componente deve ser um número menor ou igual a 0.")
                    msg.setWindowTitle("Erro na execução")
                    msg.setStandardButtons(QMessageBox.Ok)
                    retval = msg.exec_()

                    return False

        return True

    #BITRATE = 192000.
    BITRATE = 48000.

    def play_sound(self):

        if self.update_params():
            
            points = int(self.BITRATE * self.duracao)
            times = np.linspace(0, self.duracao, points, endpoint=False)

            print(self.frequencias)
            audioSignalSum = np.zeros(times.shape)

            for f in range(2):
                audioSignalSum += 10**((self.intensidades[f])/20)*np.sin(times*self.frequencias[f]*2*np.pi)*self.checkboxes[f]

            audioSignal = 10**((self.intensidades[0])/20)*np.sin(times*self.frequencias[0]*2*np.pi)*self.checkboxes[0]
            audioSignal2 = 10**((self.intensidades[1])/20)*np.sin(times*self.frequencias[1]*2*np.pi)*self.checkboxes[1]
            audioSignal3 = 10**((self.intensidades[2])/20)*np.sin(times*self.frequencias[2]*2*np.pi)*self.checkboxes[2]

            nao_zero_freq = []
            for f in self.frequencias:
                if f > 0:
                    nao_zero_freq.append(f)

            self.MPLWidget.canvas.draw()
            self.MPLWidget.update_plot(times, audioSignalSum, min(nao_zero_freq))

            self.data = np.array((audioSignal + 1.0)*127.5, dtype=np.int8).tobytes()
            self.data2 = np.array((audioSignal2 + 1.0)*127.5, dtype=np.int8).tobytes()
            self.data3 = np.array((audioSignal3 + 1.0)*127.5, dtype=np.int8).tobytes()

            if not self.tocando:
                self.tocando = True
                pyaudio = PyAudio()

                stream = pyaudio.open(
                    format=pyaudio.get_format_from_width(1),
                    channels=1,
                    rate=int(self.BITRATE),
                    output=True)


                tr = threading.Thread(target = self.play_stream, args = (stream, pyaudio, ))
                tr.start()

            if not self.tocando2:
                self.tocando2 = True
                pyaudio2 = PyAudio()

                stream2 = pyaudio2.open(
                    format=pyaudio.get_format_from_width(1),
                    channels=1,
                    rate=int(self.BITRATE),
                    output=True)


                tr2 = threading.Thread(target = self.play_stream2, args = (stream2, pyaudio2, ))
                tr2.start()

            if not self.tocando3:
                self.tocando3 = True
                pyaudio3 = PyAudio()

                stream3 = pyaudio3.open(
                    format=pyaudio.get_format_from_width(1),
                    channels=1,
                    rate=int(self.BITRATE),
                    output=True)


                tr3 = threading.Thread(target = self.play_stream3, args = (stream3, pyaudio3, ))
                tr3.start()

    def play_stream2(self, stream, pyaudio):
        while self.tocando2:
            stream.write(self.data2)
            if not self.constante:
                self.tocando2 = False
        stream.stop_stream()
        stream.close()
        pyaudio.terminate()

    def play_stream3(self, stream, pyaudio):
        while self.tocando3:
            stream.write(self.data3)
            if not self.constante:
                self.tocando3 = False
        stream.stop_stream()
        stream.close()
        pyaudio.terminate()

    def play_stream(self, stream, pyaudio):
        while self.tocando:
            stream.write(self.data)
            if not self.constante:
                self.tocando = False
        stream.stop_stream()
        stream.close()
        pyaudio.terminate()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.setWindowTitle("Simulador de Mascaramento")

    window.MPLWidget = MatplotlibWidget(window.ui.groupBox)
    
    window.MPLWidget.show()

    tr = threading.Thread(target = window.resize_plot_delay, args = (0.3, ))
    tr.start()
    
    sys.exit(app.exec_())



