from PyQt5.QtCore import QRect, QSize, Qt, QMetaObject, pyqtSignal, QFile, QTextStream, QCoreApplication
from PyQt5.QtWidgets import QWidget,QGridLayout,QLabel,QLineEdit,QFormLayout,QPushButton,QMainWindow,QApplication
from Format_Class import icon_Add
class Ui_Dialog_Ignore(QMainWindow):
    signal1 = pyqtSignal(str)
    def __init__(self,defuatquantity=5):
        super(Ui_Dialog_Ignore, self).__init__()
        self.defaultIgnoreQuantity = defuatquantity
        self.setupUi(self)
        stylesheet = self.load_stylesheet()
        if stylesheet:self.setStyleSheet(stylesheet)
    def setupUi(self, Dialog_Ignore):
        Dialog_Ignore.setObjectName("Dialog_Ignore")
        Dialog_Ignore.setWindowIcon(icon_Add("tef"))
        # Dialog_Ignore.resize(290, 250)
        Dialog_Ignore.resize(320, 350)
        Dialog_Ignore.setWindowFlags(Qt.CustomizeWindowHint|Qt.WindowStaysOnTopHint)
        screen = QApplication.desktop().screenGeometry()
        Dialog_Ignore.move((screen.width() - Dialog_Ignore.width()) // 2, 100)
        Dialog_Ignore.setFixedSize(Dialog_Ignore.width(), Dialog_Ignore.height())
        self.centralwidget = QWidget(Dialog_Ignore)
        self.centralwidget.setObjectName("centralwidget")
        self.widget = QWidget(self.centralwidget)
        # self.widget.setGeometry(QRect(0, 0, 300, 230))
        self.widget.setGeometry(QRect(0, 0, 320, 350))
        self.widget.setObjectName("widget")
        self.gridLayout = QGridLayout(self.widget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QLabel(self.widget)
        self.label.setMaximumSize(QSize(16777215, 13))
        self.label.setObjectName("label")
        self.label.setStyleSheet("#label{border-image: url(static/img/top_logo.jpg);background-color:transparent;}")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)
        self.label_Title = QLabel(self.widget)
        self.label_Title.setMaximumSize(QSize(16777215, 40))
        self.label_Title.setAlignment(Qt.AlignCenter)
        self.label_Title.setObjectName("label_Title")
        self.gridLayout.addWidget(self.label_Title, 1, 0, 1, 3)
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_Text1 = QLabel(self.widget)
        self.label_Text1.setObjectName("label_Text1")
        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_Text1)
        self.input_PC = QLineEdit(self.widget)
        self.input_PC.setMaximumSize(QSize(200, 16777215))
        # self.input_PC.setClearButtonEnabled(True)
        self.input_PC.setObjectName("input_PC")
        self.input_PC.setText(str(self.defaultIgnoreQuantity))
        self.input_PC.setAlignment(Qt.AlignCenter)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.input_PC)
        self.gridLayout.addLayout(self.formLayout, 2, 0, 1, 3)
        self.putID = ""
        self.putPSW = ""
        keys = ['1', '2', '3','4', '5', '6', '7', '8', '9','清0', '0', '确定']
        position = [(3, 0), (3, 1), (3, 2), 
                    (4, 0), (4, 1), (4, 2), 
                    (5, 0), (5, 1), (5, 2), 
                    (6, 0), (6, 1), (6, 2), ]
        for item in range(len(keys)):
            btn = QPushButton(keys[item])
            btn.setFixedSize(QSize(100, 50))
            btn.clicked.connect(self.btnClicked)
            self.gridLayout.addWidget(btn, position[item][0], position[item][1],1, 1)
        self.gridLayout.setRowStretch(7, 1)
        Dialog_Ignore.setCentralWidget(self.centralwidget)
        self.retranslateUi(Dialog_Ignore)
        QMetaObject.connectSlotsByName(Dialog_Ignore)
        self.input_PC.setFocus()
        self.input_PC.installEventFilter(self)
        self.memory_number = 0
    def showEvent(self, event):
        self.input_PC.setText(str(self.defaultIgnoreQuantity))
    def btnClicked(self):
        sender = self.sender()
        if sender.text() == "确定":
            text = self.input_PC.text()
            if text == "" or text == "0":
                text = "0"
            self.signal1.emit(text)
        elif sender.text() == "清0":
            self.input_PC.setText("0")
        else:
            self.input_PC.setText(sender.text() if self.input_PC.text() == "0" else self.input_PC.text() + sender.text())
    def resetDefaultIgnoreQuantity(self,quantity):
        self.defaultIgnoreQuantity = quantity
    def retranslateUi(self, Dialog_Ignore):
        _translate = QCoreApplication.translate
        Dialog_Ignore.setWindowTitle(_translate("Dialog_Ignore", "检测准备"))
        self.label_Title.setText(_translate("Dialog_Ignore", "检测准备"))
        self.label_Text1.setText(_translate("Dialog_Ignore", "  跳过的件数"))
    def load_stylesheet(self):
        """加载 QSS 样式表"""
        try:
            style_file = QFile("static/ui/Layout.qss")
            style_file.open(QFile.ReadOnly | QFile.Text)
            style_stream = QTextStream(style_file)
            return style_stream.readAll()
        except FileNotFoundError:
            return ""
if __name__ == "__main__":
    import sys  
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    pyqt_learn = Ui_Dialog_Ignore()
    pyqt_learn.show()
    app.exec_()