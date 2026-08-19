from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSize,QTimer
from PyQt5.QtGui import QIcon,QPixmap
from Config_Class import lang
from datetime import datetime




def add_icon(object,ico_path,w=20,h=20,static_path="static/icon/"):
    icon = QIcon(static_path + ico_path)
    object.setIcon(icon)
    object.setIconSize(QSize(w,h))
def add_open_close_icon(object,ico1_path,ico2_path,w=20,h=20,static_path="static/icon/"):
    icon = QIcon()
    icon.addPixmap(QPixmap(static_path + ico1_path), QIcon.Normal, QIcon.Off)
    icon.addPixmap(QPixmap(static_path + ico2_path), QIcon.Normal, QIcon.On)
    object.setIcon(icon)
    object.setIconSize(QSize(w,h))
def icon_Add(name):
    icon = QIcon()
    icon.addPixmap(QPixmap("static/img/"+name+".ico"), QIcon.Normal, QIcon.Off)
    return icon
def statusbar_Text():
    return f"Copyright  © 2025-{datetime.now().year} PkP/TEF1 | v4.2.0 (2025.Q1-2026.08.15) | All rights reserved."
class CustomMessageBox(QMessageBox):
    def __init__(self,  title, message,messagecolor="green",icon="noicon",button=[lang['CONPONENTS']['enter']],button_role=[2],timeout=0,parent=None):
        """自定义消息框

        Args:
            title (str): 消息框标题
            message (str): 消息框内容
            icon (str, optional): <<"noicon","question","info","warning","error">>. Defaults to "noicon".
            button (list, optional): 要添加的按钮,以list形式传递. Defaults to ("确定").
            button_role (list, optional): 按钮对应的规则,以list形式传递对应的下标:
                <<1:AcceptRole,2:RejectRole,3:YesRole,4:NoRole,5:ResetRole,6:ApplyRole,7:HelpRole,8:ActionRole>>. Defaults to (2).
            timeout(int, optional): 超时关闭(0代表不关闭,毫秒). Defaults to 0.
            parent (Object, optional): 要调用的窗口(一般填self). Defaults to None.
        """
        super().__init__(parent)
        self.Wicon=icon
        self.button_List = button
        self.button_Role = button_role
        self.timeout = timeout
        self.format_icon(self.Wicon)
        self.setWindowTitle(title)
        self.setText(message)
        # self.setWindowModality(Qt.ApplicationModal)
        #qt_msgboxex_icon_label {background: red;}
        self.setStyleSheet('''
            #qt_msgbox_label {
                font-size:20px;
                color: ''' + messagecolor + ''';
                font-weight:900;                       
            }
            
            QMessageBox {background: #fff;}
            QMessageBox QPushButton {
                padding: 2px;
                border-radius: 5px;
                background: white;
            }
            QMessageBox QPushButton:hover {background: darkCyan;}
            QMessageBox QPushButton[text="''' + lang['CONPONENTS']['cancel'] + '''"] {
                background: #71767c;
                height:30px;
                font-size:25px;
                font-weight:700;
            }
            QMessageBox QPushButton[text="''' + lang['CONPONENTS']['enter'] + '''"] {
                background: #007bc0;
                height:30px;
                font-size:25px;
                font-weight:700;
            }
            QMessageBox QPushButton[text="''' + lang['CONPONENTS']['yes'] + '''"] {
                background: #007bc0;
                height:30px;
                font-size:25px;
                font-weight:700;
            }''')
        self.add_button()
        self.schedule_close()
    def format_icon(self,icon):
        icon_type={"noicon":QMessageBox.NoIcon,
                    "question":QMessageBox.Question,
                   "info":QMessageBox.Information,
                   "warning":QMessageBox.Warning,
                   "error":QMessageBox.Critical,
                   }
        self.setIcon(icon_type[icon])
    def add_button(self):
        buttonRole=[QMessageBox.AcceptRole,
                    QMessageBox.RejectRole,
                    QMessageBox.YesRole,
                    QMessageBox.NoRole,
                    QMessageBox.ResetRole,
                    QMessageBox.ApplyRole,
                    QMessageBox.HelpRole,
                    QMessageBox.ActionRole]
        for i in range(len(self.button_List)):
            self.addButton(self.button_List[i],buttonRole[self.button_Role[i]-1])
    def schedule_close(self):
        if self.timeout > 0:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.close)
            self.timer.start(self.timeout)
