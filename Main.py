
# import argparse
# import cv2
# import numpy as np
# import onnxruntime as ort
# from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession
# from Config_Class import ConfigHandler
# from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession
from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox,QFileDialog,QListWidgetItem,QMainWindow,QApplication,QButtonGroup
from PyQt5.QtCore import QTimer,Qt,QThread,pyqtSignal,QFile,QTextStream
from PyQt5.QtGui import QColor,QPixmap,QImage,QScreen
from PyQt5.QtSvg import QSvgWidget
from pygrabber.dshow_graph import FilterGraph
from Format_Class import *
from Config_Class import *
import cv2
import math,sys
import numpy as np
from detect_onnx import YOLO11
import Dialog_IgnorePcs
from datetime import datetime
class Ui_yolo(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__()
        uic.loadUi("static/ui/Cylinder.ui",self)
        self.labelsJson = JsonFile("static/config/labels.json").read_json_file()
        self.config = ConfigHandler()
        self.ui_inital()
        self.inital()
        self.checklist={"Camera":None,"GPU":None}
        self.cameraIndex = 0
        self.started = False
        self.currentTabIndex = 0
        self.currentResultIndex = 0#检测后listwidget的结果
        self.loadSvgWidget = None
        self.predict = False
        self.realCheck = False
        self.autoInspect = False
        self.mod =None
        self.winMax = True
        self.pauseDetect = True
        self.manualTime = None #放时间(防止用户频繁点击手动检测)
        self.resultListTime = None #历史结果列表单击事件
        self.predictCandidates = []
        self.predictFrames = 3
        self.inspectTriggerSeq = 0
        self.currentPredictTriggerSeq = 0
        self.ignoreActivatedTriggerSeq = 0
        # SaveJsonImage(None).clear_folder((self.configPath.get('sourcepredictimgpath'),self.configPath.get('sourcepredictlabelpath')))
    def ui_inital(self):
        # self.setMaximumSize(size.width(),size.height())
        self.setWindowIcon(icon_Add("tef"))
        title = lang['LAYOUT']['title']
        langYolo = lang['YOLO']
        self.label_top.setStyleSheet("#label_top{border-image: url(static/img/top_logo.jpg);background-color:transparent;}")
        self.setWindowTitle(title)
        self.label_title.setText(title)

        self.tabWidget.setTabText(0,langYolo['hardware_detection'])
        # self.tabWidget.setTabText(1,langYolo['model_train'])
        self.tabWidget.setTabText(2,langYolo['model_predict'])
        # self.tabWidget.setTabText(3,langYolo['other'])
        self.tabWidget.tabBar().setTabVisible(1, False)
        self.tabWidget.tabBar().setTabVisible(3, False)
        self.checkBox_tab3_continuous_detect.setVisible(False)
        self.btn_tab3_save_records.setVisible(False)
        self.btn_tab3_changeerror.setVisible(False)
        self.frame_2.setVisible(False)
        self.frame_tab1_gpu_check_2.setVisible(False)
        # self.checkBox_tab3_continuous_detect.setEnabled(True)
        # self.btn_tab4_other2.setVisible(False)
        

        self.label_tab1_camera_check_title.setText(langYolo['cameras'])
        self.label_tab1_gpu_check_title.setText(langYolo['gpus'])
        self.label_tab1_savepicture_pathtitle.setText(langYolo['img_saving_path'])
        self.btn_tab1_savepicture_path.setText(langYolo['img_saveas'])
        self.label_tab1_px.setText(langYolo['resolution'])
        self.btn_tab1_opencamera.setText(langYolo['open_cv'])
        self.btn_tab1_takepicture.setText(langYolo['take_picture'])
        self.btn_tab1_closecamera.setText(langYolo['close_cv'])
        self.label_tab1_camera_check_title.setText(langYolo['cameras'])
        self.label_tab1_camera_check_title.setText(langYolo['cameras'])
        self.label_tab1_camera_check_title.setText(langYolo['cameras'])
        
        self.groupBox_tab3_setting.setTitle(langYolo['records'])
        self.label_tab3_selectmodel.setText(f"{langYolo['model']}:")
        self.btn_tab3_manual_predict.setText(langYolo['single_manual_predict'])
        self.btn_tab3_cancleWarn.setVisible(False)
        self.btn_tab3_cancleWarn.setText(langYolo['cancel_warn'])
        self.checkBox_tab3_continuous_detect.setText(langYolo['continuous_detect'])
        self.btn_tab3_start.setText(langYolo['prepare_detect'])
        self.btn_tab3_changeerror.setText(langYolo['rectify'])
        self.btn_tab3_clear_picture_win.setText(langYolo['clear'])
        self.btn_tab3_save_records.setToolTip(langYolo['save_records'])
        self.btn_tab3_clear_records.setToolTip(langYolo['clear_records'])
        self.radioButton_tab3_continue.setText(langYolo['continue_check'])
        self.radioButton_tab3_pausereset.setText(langYolo['pause_check_reset'])
        self.radioButton_tab3_pause.setText(langYolo['pause_temp_check'])
        
        self.tab3_btn_group = QButtonGroup(self)
        self.tab3_btn_group.addButton(self.radioButton_tab3_continue)
        self.tab3_btn_group.addButton(self.radioButton_tab3_pausereset)
        self.tab3_btn_group.addButton(self.radioButton_tab3_pause)
        self.radioButton_tab3_pausereset.setStyleSheet("background-color: red;")
        self.set_pause_controls_enabled(False)

        add_icon(self.btn_tab1_refresh_camera,"refresh.ico",20,20)
        add_icon(self.btn_tab3_save_records,"save.ico",30,30)
        add_icon(self.btn_tab3_clear_records,"remove.ico",30,30)
        add_icon(self.btn_tab3_refresh_model,"refresh.ico",20,20)
        self.statusbar.showMessage(statusbar_Text())
    def set_pause_controls_enabled(self,enabled):
        self.radioButton_tab3_continue.setEnabled(enabled)
        self.radioButton_tab3_pausereset.setEnabled(enabled)
        self.radioButton_tab3_pause.setEnabled(enabled)
    def inital(self,parent=None):
        self.usbConfig = self.config.get_all_config('USB')
        self.config_config = self.config.get_all_config('config')
        self.configPath = self.config.get_all_config('Path')
        self.okresult = self.config_config.get("okresult").split(",") #合格结果
        self.ngcolor = list(map(int,self.config_config.get("ngcolor","255,0,0").split(",")))
        self.scorenotmetcolor = list(map(int,self.config_config.get("scorenotmetcolor","255,207,0").split(",")))
        # self.substituteResult = self.config_config.get("substitute")
        self.labelName = self.config_config.get("label")
        self.defaultIgnoreQuantity = self.config_config.get("defaultignorequantity",5)
        self.result_path = self.configPath.get("results","./result")
        self.px_w = int(self.config_config.get("px_w",640))
        self.px_h = int(self.config_config.get("px_h",480))
        config_lowlimit = float(self.config_config.get('lowerlimit',0.5))
        confidence = float(self.config_config.get("confidence"))
        try:
            self.predictFrames = max(1, int(self.config_config.get("predictframes", 3)))
        except Exception:
            self.predictFrames = 3

        try:
            self.ignoreQuantity = int(self.defaultIgnoreQuantity)
        except ValueError:
            self.ignoreQuantity = 5
        self.classes = self.labelsJson.get(self.labelName)
        self.classNames = list(self.classes.keys())
        
        # SaveJsonImage(None).clear_folder((self.configPath.get('sourcepredictimgpath'),self.configPath.get('sourcerectifyimgpath')))
        self.comboBox_tab3_results.setVisible(False)
        if config_lowlimit >= confidence:
            self.write_temp_txt()
            QMessageBox.warning(self,lang['TITLE']['warning'],lang['MESSAGE']['error_confidence'])
            sys.exit()
            return
        # if self.substituteResult not in self.classes:
        #     self.btn_tab3_start.setEnabled(False)
        #     self.btn_tab3_start.setStyleSheet("#btn_tab3_start{background-color:#c1c7cc;color:#7d8287}")
        #     return QMessageBox.warning(self,lang['TITLE']['warning'],lang['MESSAGE']['error_substitute'])
        results = ["NG"] + self.classNames
        self.comboBox_tab3_results.addItems(results)
        self.tab3_inital_model_combobox()
        
    def tab3_inital_model_combobox(self):
        self.comboBox_tab3_model.clear()
        for filename in os.listdir('static/model'):
            if filename.endswith(".onnx"):
                base_filename, _ = os.path.splitext(filename)
                self.comboBox_tab3_model.addItem(base_filename)
        self.cacheModelName = self.configPath.get('modelname')
        if self.cacheModelName:
            self.comboBox_tab3_model.setCurrentText(self.cacheModelName)
    def clicked_event(self):
        self.listWidget_tab1_camera_check.itemClicked.connect(self.tab1_camera_list_item)
        self.listWidget_tab1_gpu_check.itemClicked.connect(self.tab1_gpu_list_item)
        self.btn_tab1_refresh_camera.clicked.connect(self.tab1_refresh_camera)
        self.btn_tab1_opencamera.clicked.connect(self.tab1_open_camera)
        self.btn_tab1_closecamera.clicked.connect(self.close_camera)
        self.btn_tab1_savepicture_path.clicked.connect(self.select_folder_path)
        self.btn_tab1_takepicture.clicked.connect(self.tab1_take_picture)
        self.comboBox_tab1_px.currentIndexChanged.connect(self.tab1_change_px)
        self.tabWidget.currentChanged.connect(self.onTabChanged)
        self.btn_tab3_start.clicked.connect(self.tab3_start_predict)
        self.comboBox_tab3_model.currentIndexChanged.connect(self.tab3_change_model)
        self.btn_tab3_manual_predict.clicked.connect(lambda:self.tab3_manual_predict(False))
        self.btn_tab3_cancleWarn.clicked.connect(self.release_warning)
        self.checkBox_tab3_continuous_detect.stateChanged.connect(self.tab3_on_checkbox_changed)
        self.btn_tab3_clear_picture_win.clicked.connect(self.tab3_clear_picture_win)
        self.btn_tab3_changeerror.clicked.connect(self.tab3_show_rectify_result)
        self.listWidget_tab3_result.itemClicked.connect(self.tab3_listItem_event)
        self.btn_tab3_save_records.clicked.connect(self.tab3_save_records)
        self.btn_tab3_clear_records.clicked.connect(self.tab3_clear_records)
        self.btn_tab3_refresh_model.clicked.connect(self.tab3_inital_model_combobox)
        self.tab3_btn_group.buttonClicked.connect(self.tab3_pause_detect)
        self.comboBox_tab3_results.currentIndexChanged.connect(self.tab3_rectify_result)
        self.btn_teflogo.clicked.connect(self.windowsChange)
    def write_temp_txt(self):
        with open("static/temp.txt","w",encoding="utf-8") as f:
            f.write("1")
        
    def showEvent(self, event):
        """在页面显示完成后执行的代码"""
        super().showEvent(event)
        if self.isVisible():  # 确保页面可见时执行
            if self.started:
                return
            self.tab3_clear_records()
            self.started = True
            graph = FilterGraph()
            self.checkCamera = CheckCamera(graph)
            self.checkCamera.signal_camera_list.connect(self.tab1_camera_list)
            self.clicked_event()
            self.cameraPix = ()#(480, 640, 3)
            self.cap = None
            self.timer = QTimer()
            self.timer.timeout.connect(lambda:self.update_frame(self.label_tab1_camera_win))
            self.checkCamera.start()
            self.write_temp_txt()
            self.dialog = None 

    def closeEvent(self,event):
        msgresult = CustomMessageBox(lang['TITLE']['exit'],lang['ENQUIRE']['exit'],messagecolor="#007bc0",icon="question",button=[lang['CONPONENTS']['yes'],lang['CONPONENTS']['cancel']],button_role=[1,2],timeout=8000,parent=self).exec()
        if msgresult == 0:
            try:
                if self.cap:
                    self.close_camera()
                if self.mod:
                    self.mod.resetUsb_value()
            except Exception as e:
                WriteErrorLogs(str(e) + "[closeEvent]")
            self.close_dialog()
            event.accept()
        else:
            event.ignore()
    def windowsChange(self):
        """窗口最大化或标准化"""
        if self.winMax:
            self.showMaximized()
            self.winMax = False
        else:
            self.showFullScreen()
            self.winMax = True
    def tab3_clear_picture_win(self):
        self.currentResultIndex = 0
        self.label_tab3_result_name.clear()
        self.label_tab3_picture_win.clear() 
        self.label_tab3_result.clear()
        self.label_tab3_result.setStyleSheet(f"background-color:rgb(255,207,0);color:#fff")
    def tab3_show_rectify_result(self):#弃用
        """_summary_:#弃用 
        """
        def hide_rectify_result():self.comboBox_tab3_results.setVisible(False)
        resultText = self.label_tab3_result.text()
        if resultText == "NG" or resultText == "":
            return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['no_target'],messagecolor="#8f7300",icon="warning",timeout=1000,parent=self).exec()
        self.rectifyTimer = QTimer(self)
        self.rectifyTimer.setSingleShot(True)
        self.rectifyTimer.timeout.connect(hide_rectify_result)
        self.rectifyTimer.start(10000)
        self.comboBox_tab3_results.setVisible(True)
    def tab3_rectify_result(self,index):#弃用
        """#弃用 
        """
        return
        try:
            if not self.comboBox_tab3_results.isVisible():return
            selected_text = self.comboBox_tab3_results.currentText()
            if selected_text == self.label_tab3_result.text():return
            if selected_text not in self.classes: return
            item = self.listWidget_tab3_result.item(self.currentResultIndex)
            self.tab3_save_predict_result(item.text(),selected_text,True,item)
            self.rectifyTimer.stop()
            self.comboBox_tab3_results.setVisible(False)
        except Exception as e:
            WriteErrorLogs(str(e) + "[tab3_rectify_result]")
            return
    def signal_save_result(self,status):
        if not status.get('status'):
            WriteErrorLogs(str(status.get('msg', 'unknown save result fail')) + "[signal_save_result]")
            return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['save_result_fail'],messagecolor="#8f7300",icon="warning",timeout=3000,parent=self).exec()
        try:
            if self.saveResult:
                self.saveResult = None
        except Exception as e:
            WriteErrorLogs(str(e) + "[signal_save_result cleanup]")
    
    def tab3_save_predict_result(self,frame,draw_img,timestamp,result,rectify=False,item=None,confidence=0,box=[0,0,0,0]):
        """_summary_:#弃用 
        """
        saveResult = SaveJsonImage(f"IMG_{timestamp}")
        imgPath = self.configPath['sourcepredictimgpath']
        labelPath = self.configPath['sourcepredictlabelpath']

        if not rectify:
            saveResult.save_image(imgPath,self.sourceFrame)
            if result == "NG":return
            x1, y1, x2, y2 = box
            self.startPoint,self.endPoint = (float(x1),float(y1)),(float(x2),float(y2))
            saveResult.save_json(labelPath,result,self.startPoint,self.endPoint,confidence)
        else:
            if result == "NG":return
            rectifyimgPath = self.configPath['sourcerectifyimgpath']
            rectifylabelPath = self.configPath['sourcerectifylabelpath']
            _imgPath = f"{imgPath}/IMG_{timestamp}.jpg"
            if os.path.exists(_imgPath):
                shutil.copy(_imgPath, os.path.join(rectifyimgPath, f"IMG_{timestamp}.jpg"))
                _labelPath = f"{labelPath}/IMG_{timestamp}.json"
                results = JsonFile(_labelPath).read_json_file()
                results['shapes'][0]['label'] = result
                saveResult.write_json_file(_labelPath,results)

                shutil.copy(_labelPath, os.path.join(rectifylabelPath, f"IMG_{timestamp}.json"))
                self.predict_result(result,addList=False,current_item=item)

    def tab3_save_records(self):#弃用
        """_summary_:已弃用
        """
        SaveJsonImage(None).save_txt()
        self.tab3_clear_picture_win()
        self.listWidget_tab3_result.clear()

    def tab3_clear_records(self):
        try:
            # SaveJsonImage(None).clear_folder((self.configPath.get('sourcepredictimgpath'),self.configPath.get('sourcepredictlabelpath')))
            self.tab3_clear_picture_win()
            self.listWidget_tab3_result.clear()
        except Exception as e:
            WriteErrorLogs(str(e) + "[tab3_clear_records]")
            return
    def select_folder_path(self):
        folder_selected = QFileDialog.getExistingDirectory(self, lang['TITLE']['saveas'])
        if folder_selected:
            self.plainTextEdit_tab1_savepicture_path.setPlainText(folder_selected)
    def tab1_change_px(self,index):
        selected_text = self.comboBox_tab1_px.currentText()
        if selected_text == "AUTO":
            pass
        else:
            size = selected_text.split("x")
            self.cameraPix = (int(size[0]),int(size[1]))
    def tab3_on_checkbox_changed(self, state):
        if state == Qt.Checked:
            self.realCheck = True
            self.btn_tab3_manual_predict.setEnabled(False)
        else:
            self.realCheck = False
            self.btn_tab3_manual_predict.setEnabled(True)
    def clear_radio_style(self):
        # 清除所有单选框的背景色
        self.radioButton_tab3_continue.setStyleSheet("")
        self.radioButton_tab3_pausereset.setStyleSheet("")
        self.radioButton_tab3_pause.setStyleSheet("")
    def tab3_pause_detect(self,button):
        try: 
            tooltip = button.toolTip()
            if tooltip == "0":
                self.show_dialog()
            else:
                self.clear_radio_style()
                button.setChecked(True)
                self.pauseDetect = True
                color = "yellowlightid"
                if tooltip == "1":
                    self.ignoreQuantity = int(self.defaultIgnoreQuantity)
                    self.label_tab3_loop.setText(str(self.ignoreQuantity))
                    self.radioButton_tab3_pausereset.setStyleSheet("background-color: red;")
                elif tooltip == "2":
                    self.radioButton_tab3_pause.setStyleSheet("background-color:#ffcf00")
                    self.label_tab3_loop.setVisible(False)
                self.reset_senser_status(color)
        except Exception as e:
            WriteErrorLogs(str(e) + "[tab3_pause_detect]")
            return

    def show_dialog(self):
        if self.dialog and self.dialog.isVisible():
            self.dialog.activateWindow()  # 激活窗口
            self.dialog.raise_()         # 将窗口置于顶层
            return
        self.dialog = Dialog_IgnorePcs.Ui_Dialog_Ignore(self.ignoreQuantity)
        self.dialog.signal1.connect(self.receive_ignorepcs)
        self.dialog.show()
    def close_dialog(self):
        try:
             if self.dialog and self.dialog.isVisible():
                self.dialog.close()
                self.dialog.destroy()
                self.dialog = None
        except Exception as e:
            WriteErrorLogs(str(e) + "[close_dialog]")
            return
    def receive_ignorepcs(self,pcValue):
        self.ignoreQuantity = int(pcValue)
        # Exclude triggers already emitted before confirmation. The next sensor trigger
        # gets a larger sequence number and must consume one ignore quantity.
        self.ignoreActivatedTriggerSeq = self.inspectTriggerSeq
        if self.is_material_currently_sensed() and hasattr(self, 'monitorSenser') and self.monitorSenser:
            # The material already present at confirmation is the current item, not a
            # new trigger. Keep it latched until it leaves the pallet sensor.
            self.monitorSenser.initStrainerSensorStatus = True
        self.label_tab3_loop.setVisible(True if self.ignoreQuantity > 0 else False)
        self.label_tab3_loop.setText(str(self.ignoreQuantity))
        self.clear_radio_style() 
        self.radioButton_tab3_continue.setStyleSheet("background-color: green;")
        self.pauseDetect = False
        color = "greenlightid" 
        self.reset_senser_status(color)
        self.close_dialog()   
    def is_material_currently_sensed(self):
        try:
            if not (self.mod and self.usbConfig):
                return False

            pallet_sensor_id = self.usbConfig.get('palletsenserid')
            senser_id = self.usbConfig.get('senserid')
            if pallet_sensor_id is None or senser_id is None:
                return False

            pallet_result = self.mod.getUsb_value(pallet_sensor_id)
            senser_result = self.mod.getUsb_value(senser_id)
            if not pallet_result.get('status') or not senser_result.get('status'):
                return False

            # Align with trigger condition: both pallet sensor and material sensor are active.
            return bool(pallet_result.get('data')) and bool(senser_result.get('data'))
        except Exception as e:
            WriteErrorLogs(str(e) + "[is_material_currently_sensed]")
        return False
    def reset_senser_status(self,color):
        try:
            if self.monitorSenser.isRunning():
                self.monitorSenser.pause(self.pauseDetect)
                self.change_light(color)
        except Exception as e:
            WriteErrorLogs(str(e) + "[reset_senser_status]")
    def change_light(self,light_name):
        lights=('redlightid','greenlightid','yellowlightid')
        if light_name == "redlightid":self.mod.setUsb_value(self.usbConfig.get('stopmacineid'),'1')
        for light in lights:
            value = '1' if light == light_name else '0'
            self.mod.setUsb_value(self.usbConfig.get(light),value)
    def tab1_refresh_camera(self):
        self.listWidget_tab1_camera_check.clear()
        self.checkCamera.start()
    def tab3_change_model(self,index):
        selected_model = self.comboBox_tab3_model.currentText()
        self.config.set_config('Path','modelname',selected_model)
        if self.realCheck:
            self.checkBox_tab3_continuous_detect.setChecked(False)
        self.close_camera()
        self.tab3_pause_detect(self.radioButton_tab3_pausereset)
    def tab3_manual_predict(self,AUTO_INSPECT=False):
        now = datetime.now()
        if not AUTO_INSPECT and self.manualTime and (now- self.manualTime).total_seconds()<int(self.config_config.get('clicktimeout')):return CustomMessageBox(lang['TITLE']['warning'],f"Try again in {int(self.config_config.get('clicktimeout'))} seconds",messagecolor="#725b00",icon="warning",timeout=2000,parent=self).exec()
        self.currentResultIndex = 0
        self.autoInspect = AUTO_INSPECT
        self.currentPredictTriggerSeq = self.inspectTriggerSeq if AUTO_INSPECT else 0
        self.predictCandidates = []
        if self.cap:
            self.show_loading(self.label_tab3_picture_win)
            self.predict = True
            self.manualTime = now

    def pick_best_candidate(self,candidates):
        valid_candidates = [c for c in candidates if c.get('result') != "NG" and c.get('confidence') is not None]
        if valid_candidates:
            return max(valid_candidates, key=lambda x: x.get('confidence', 0))
        return {
            "img": candidates[-1].get("img") if candidates else None,
            "draw_img": candidates[-1].get("draw_img") if candidates else None,
            "result": "NG",
            "confidence": None,
            "floatboxe": [0,0,0,0]
        }

    def tab3_listItem_event(self,item):
        now = datetime.now()
        try:
            if self.resultListTime and (now- self.resultListTime).total_seconds()<int(self.config_config.get('clicktimeout')):return CustomMessageBox(lang['TITLE']['warning'],f"Try again in {int(self.config_config.get('clicktimeout'))} seconds",messagecolor="#725b00",icon="warning",timeout=2000,parent=self).exec()
            value = item.text()
            item_color = item.background().color()
            self.label_tab3_result_name.setText(value)
            day_folder_name = f"{value[:8]}"
            file_name = f"IMG_{value}.jpg"
            img_path = os.path.join(self.result_path,"01_detection_results",day_folder_name,file_name)
            self.label_tab3_picture_win.clear()
            if not os.path.exists(img_path): return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['no_result'],messagecolor="#8f7300",icon="warning",timeout=1000,parent=self).exec()
            pixmap = QPixmap(img_path)
            if pixmap.isNull(): return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['no_result'],messagecolor="#8f7300",icon="warning",timeout=1000,parent=self).exec()
            scaled_pixmap = pixmap.scaled(
                self.label_tab3_picture_win.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label_tab3_picture_win.setPixmap(scaled_pixmap)
            self.label_tab3_picture_win.setAlignment(Qt.AlignCenter)
            source_json_path = os.path.join(self.result_path,"02_detection_datasets","source_json",f"IMG_{value}.json")
            text = "NG"
            if os.path.exists(source_json_path):
                json_data = JsonFile(source_json_path).read_json_file()
                if json_data.get('shapes'):
                    try:
                        text = json_data['shapes'][0]['label']
                    except Exception as e:
                        WriteErrorLogs(str(e) + "[tab3_listItem_event parse_label]")
            self.label_tab3_result.setText(text)
            self.label_tab3_result.setStyleSheet(f"background-color:{item_color.name()};color:#fff")
            self.resultListTime = now
        except Exception as e:
            self.resultListTime = now
            WriteErrorLogs(str(e) + "[tab3_listItem_event]")
            return CustomMessageBox(lang['TITLE']['warning'],str(e),messagecolor="red",icon="error",timeout=5000,parent=self).exec()
            


        
    def show_loading(self,label):
        return
        self.loadSvgWidget = QSvgWidget(label,minimumHeight=200,minimumWidth=200,visible=True)
        self.loadSvgWidget.load('static/img/Svg_icon_loading.svg')
        window_width = label.width()
        window_height = label.height()
        widget_width = self.loadSvgWidget.width()
        widget_height = self.loadSvgWidget.height()
        x_pos = (window_width - widget_width) // 2
        y_pos = (window_height - widget_height) // 2
        self.loadSvgWidget.move(x_pos, y_pos)
    def close_loading(self):
        return
        try:
            self.loadSvgWidget.setVisible(False)
            self.loadSvgWidget = None
        except Exception as e:
            WriteErrorLogs(str(e) + "[close_loading]")
    def current_tab_index(self):
        return self.label_tab1_camera_win if self.currentTabIndex == 0 else self.label_tab3_camera_win
    def start_camera(self,index):#启动相机
        if self.cap is not None:  # 避免重复启动摄像头
            return
        self.show_loading(self.current_tab_index())
        self.capStart = StartCapture(index)
        self.capStart.signal_status.connect(self.signal_capture)
        self.capStart.start()
    def close_camera(self):
        if self.currentTabIndex == 0:self.label_tab1_camera_win.clear()
        elif self.currentTabIndex == 2:self.label_tab3_camera_win.clear()
        if self.mod:self.change_light(None)
        self.set_pause_controls_enabled(False)
        if self.cap:
            self.timer.stop()
            self.cap.release()
            cv2.destroyAllWindows()
            self.cap = None
            self.closeMonitorThread()
    def closeMonitorThread(self):
        try:
            if hasattr(self, 'monitorSenser') and self.monitorSenser and self.monitorSenser.isRunning():
                self.monitorSenser.stop()
                self.monitorSenser.wait(1000)
        except Exception as e:
            WriteErrorLogs(str(e) + "[closeMonitorThread]")
    def tab1_open_camera(self):
        if self.loadSvgWidget:return
        if not self.checklist['Camera']: return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['select_cv'],messagecolor="#8f7300",icon="warning",timeout=2000,parent=self).exec()
        self.start_camera(self.cameraIndex)
    def tab1_take_picture(self):
        path = self.plainTextEdit_tab1_savepicture_path.toPlainText()
        if not self.cap:return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['select_cv'],messagecolor="#8f7300",icon="warning",timeout=2000,parent=self).exec()
        if not path: 
            CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['picture_path'],messagecolor="#8f7300",icon="warning",timeout=3000,parent=self).exec()
            self.select_folder_path()
            return 
        path_avalible = is_path_accessible(self.plainTextEdit_tab1_savepicture_path.toPlainText())
        if not path_avalible:return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['fail_picture_path'],messagecolor="#8f7300",icon="warning",timeout=3000,parent=self).exec()
        ret,frame = self.cap.read()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        img_filename = f"IMG_{timestamp}.jpg"
        # height, width = frame.shape[:2]
        # original_frame = self.resize_cv(frame,width,height,640,640)
        result = cv2.imwrite(os.path.join(path, img_filename), frame)
        
        if result:
            CustomMessageBox(lang['TITLE']['notic'],lang['MESSAGE']['success_picture_save'],messagecolor="#00884a",icon="info",timeout=800,parent=self).exec()
        else:
            CustomMessageBox(lang['TITLE']['notic'],'Failed',messagecolor="#00884a",icon="error",timeout=800,parent=self).exec()
    def resize_cv(self,frame,width:int,height:int,new_width:int,new_height:int):
        heightRatio = new_height / height
        widthRatio = new_width / width
        ratio = widthRatio if widthRatio > heightRatio else heightRatio
        _new_width, _new_height = int(width * ratio), int(height * ratio)
        
        resized_frame = cv2.resize(frame, (_new_width, _new_height),interpolation=cv2.INTER_LANCZOS4)# 对帧进行缩放
        center_x, center_y = _new_width // 2, _new_height // 2
        halfWidth = new_width // 2
        halfHeight = new_height // 2
        cropped_frame = resized_frame[
            center_y - halfHeight:center_y + halfHeight,
            center_x - halfWidth:center_x + halfWidth
        ] 
        original_frame = cv2.resize(cropped_frame, (new_width, new_height),interpolation=cv2.INTER_LANCZOS4)# 确保裁剪结果是640x640
        return original_frame
    def onTabChanged(self,index):
        self.close_camera()
        if self.currentTabIndex == 0:
            self.label_tab1_camera_win.clear()
        self.tab3_pause_detect(self.radioButton_tab3_pausereset)
        self.currentTabIndex = index
        if self.loadSvgWidget:self.close_loading()


    def tab1_camera_list(self,ls):
        count = len(ls)
        if count>0:
            for cam in ls:
                item = QListWidgetItem(self.listWidget_tab1_camera_check)
                item.setText(cam) 
        self.label_tab1_camera_check_des.setText(f"{lang['YOLO']['num_camreas']}：{count}")
    
    def tab1_gpu_list(self,ls):
        count = len(ls)
        if count>0:
            for gpu in ls:
                item = QListWidgetItem(self.listWidget_tab1_gpu_check)
                item.setText(gpu)  
        self.label_tab1_gpu_check_des.setText(f"{lang['YOLO']['num_gpu']}：{count}")
    
    def tab1_camera_list_item(self,item):#相机清单单击=>打开相机
        row = self.listWidget_tab1_camera_check.row(item) 
        self.cameraIndex = row
        if not self.checklist['Camera']:
            self.checklist['Camera'] = item
        elif self.checklist['Camera'] == item:
            item.setSelected(False)
            self.checklist['Camera'] = None
        else:
            self.checklist['Camera'] = item
            self.close_camera()
        # self.set_status_config()
    def tab1_gpu_list_item(self,item):#未启用
        if not self.checklist['GPU']:
            self.checklist['GPU'] = item
        elif self.checklist['GPU'] == item:
            item.setSelected(False)
            self.checklist['GPU'] = None
        else:
            self.checklist['GPU'] = item
        self.set_status_config()
    # def set_status_config(self):
    #     text = ""
    #     for key,value in self.checklist.items():
    #         text = f"{text} | {key}:{value.text() if value else '--'}"
    #     self.label_config.setText(text)
    
    def signal_capture(self,status):
        self.close_loading()
        if not status['status']:
            WriteErrorLogs(str(status.get('msg', 'capture start failed')) + "[signal_capture]")
            CustomMessageBox(lang['TITLE']['warning'],status['msg'],messagecolor="red",icon="error",timeout=2000,parent=self).exec()
        else:
            self.cap = status['data']
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.px_w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.px_h)
            ret,frame = self.cap.read()
            if not ret:
                WriteErrorLogs("initial cap.read() failed[signal_capture]")
                self.close_camera()
                self.change_light(None)
                return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['fail_open_cv'],messagecolor="red",icon="error",timeout=5000,parent=self).exec()
            height, width = frame.shape[:2]
            if width < self.px_w or height < self.px_h:
                WriteErrorLogs(f"camera resolution too small({width}x{height}) expected({self.px_w}x{self.px_h})[signal_capture]")
                return CustomMessageBox(lang['TITLE']['error'],lang['MESSAGE']['resolution_small'],messagecolor="red",icon="error",timeout=5000,parent=self).exec()
            if self.currentTabIndex == 2:
                try:
                    self.timer.timeout.disconnect()
                except TypeError:
                    WriteErrorLogs("timer timeout disconnect TypeError ignored[signal_capture]")
                    pass
                self.timer.timeout.connect(lambda:self.update_frame(self.current_tab_index()))
            self.timer.start(30)
    def log_sharpen(self,image, ksize=2,sigma=1.0):
        # 创建高斯模糊核
        gaussian = cv2.getGaussianKernel(ksize, sigma)
        gaussian = gaussian @ gaussian.T  # 转换为二维高斯核
        
        # 应用高斯模糊
        blurred = cv2.filter2D(image, -1, gaussian)
        
        # 创建拉普拉斯核
        laplacian = np.array([[0, -1, 0],
                            [-1, 4, -1],
                            [0, -1, 0]])
        
        # 应用拉普拉斯锐化
        sharpened = cv2.filter2D(blurred, -1, laplacian)
        
        # 将锐化结果叠加到原图上（这里简单相加，可能需要调整比例）
        result = cv2.addWeighted(image, 1.0, sharpened, 0.5, 0)
        
        return result
    def update_frame(self,label):
        if not self.cap:
            return
        ret, sframe = self.cap.read()
        if not ret or sframe is None:
            WriteErrorLogs("cap.read() failed during loop[update_frame]")
            self.close_camera()
            self.change_light(None)
            return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['fail_open_cv'],messagecolor="red",icon="error",timeout=5000,parent=self).exec()
        frame = sframe.copy()
        # frame = self.log_sharpen(frame)    
        height, width = frame.shape[:2]
        if self.currentTabIndex == 0:
            frame_width = label.width() - 4
            if frame_width <= 0:
                return
            pr = width/frame_width
            new_height = height/pr
            original_frame = cv2.resize(frame, (int(frame_width), int(new_height)),interpolation=cv2.INTER_LANCZOS4)
            convertToQtFormat = self.set_pix(original_frame,label)
        elif self.currentTabIndex == 2:
            frame_width = self.label_tab3_camera_win.width() - 4
            if frame_width <= 0:
                return
            pr = width/frame_width
            new_height = height/pr
            resized_frame = cv2.resize(frame.copy(), (int(frame_width), int(new_height)),interpolation=cv2.INTER_LANCZOS4)
            if self.realCheck and hasattr(self, 'yoloModel'):#这里如果启用需要重构，暂时先这样写
                # self.sourceFrame = self.resize_cv(frame,width,height,640,640)
                self.sourceFrame = frame
                try:
                    img,predictResult,confidence,box,floatboxe = self.yoloModel.predict(self.sourceFrame.copy())
                except Exception as e:
                    WriteErrorLogs(str(e) + "[update_frame realCheck]")
                    return
                if predictResult != "NG":
                    draw_img = self.yoloModel.draw_detections(img,box,confidence,predictResult)
                else:
                    draw_img = img
                result_resized_frame,r,(t,_) = self.yoloModel.letterbox(draw_img,(int(new_height), int(frame_width)))
                convertToQtFormat = self.set_pix(result_resized_frame,label)
                self.label_tab3_picture_win.setPixmap(convertToQtFormat)
            else:
                convertToQtFormat = self.set_pix(resized_frame,label)
            
            if self.predict:
                if self.ignoreQuantity>0 and self.autoInspect and self.currentPredictTriggerSeq > self.ignoreActivatedTriggerSeq:# and self.label_tab3_loop.isVisible():
                    self.ignoreQuantity -= 1
                    self.predict = False
                    self.predictCandidates = []
                    self.label_tab3_loop.setText(str(self.ignoreQuantity))
                    if self.ignoreQuantity == 0:
                        self.label_tab3_loop.setVisible(False)
                    self.close_loading()
                    return
                if self.listWidget_tab3_result.count()>int(self.config_config.get('historynum')):
                    self.tab3_clear_records()
                # self.sourceFrame = self.resize_cv(frame,width,height,640,640)
                self.sourceFrame = frame
                if not hasattr(self, 'yoloModel'):
                    return
                try:
                    img,predictResult,confidence,box,floatboxe = self.yoloModel.predict(self.sourceFrame.copy())
                except Exception as e:
                    WriteErrorLogs(str(e) + "[update_frame predict]")
                    self.predict = False
                    self.predictCandidates = []
                    self.close_loading()
                    return
                draw_img = img if predictResult == "NG" else self.yoloModel.draw_detections(img,box,confidence,predictResult)
                self.predictCandidates.append({
                    "img": img,
                    "draw_img": draw_img,
                    "result": predictResult,
                    "confidence": confidence,
                    "floatboxe": floatboxe
                })
                if len(self.predictCandidates) < self.predictFrames:
                    result_resized_frame,r,(t,_) = self.yoloModel.letterbox(draw_img,(int(new_height), int(frame_width)))
                    convertToQtFormat = self.set_pix(result_resized_frame,label)
                    self.label_tab3_picture_win.setPixmap(convertToQtFormat)
                    return

                self.predict = False
                best = self.pick_best_candidate(self.predictCandidates)
                self.predictCandidates = []
                self.close_loading()

                draw_img = best.get("draw_img") if best.get("draw_img") is not None else draw_img
                predictResult = best.get("result", "NG")
                confidence = best.get("confidence")
                floatboxe = best.get("floatboxe", [0,0,0,0])
                result_resized_frame,r,(t,_) = self.yoloModel.letterbox(draw_img,(int(new_height), int(frame_width)))
                convertToQtFormat = self.set_pix(result_resized_frame,label)
                self.label_tab3_picture_win.setPixmap(convertToQtFormat)
                timestamp = self.predict_result(predictResult,confidence)    
                if timestamp:
                    self.saveResult = ThreadSaveResults(self.result_path,frame,draw_img,timestamp,predictResult,None,None,confidence=confidence,box=floatboxe)
                    self.saveResult.signal_status.connect(self.signal_save_result)
                    self.saveResult.start()
                    # self.tab3_save_predict_result(frame,draw_img,timestamp,predictResult,confidence=confidence,box=floatboxe)
                return

    def tab3_start_predict(self):
        # if
        if not self.checklist['Camera']: return CustomMessageBox(lang['TITLE']['warning'],lang['MESSAGE']['select_cv'],messagecolor="#8f7300",icon="warning",timeout=2000,parent=self).exec()
        curModel = self.comboBox_tab3_model.currentText()
        self.yoloModel = YOLO11(f"{self.configPath.get('modelpath')}/{curModel}.onnx",self.classes)
        self.yoloModel.load_model() 
        self.start_camera(self.cameraIndex)

        #初始化modbus
        try:
            from USB import UsbDio
            self.mod = UsbDio(self.usbConfig)
            state = self.mod.inital_device()
            if not state['status']:
                self.mod = None
                self.set_pause_controls_enabled(False)
                WriteErrorLogs(str(state.get('msg', 'usb init failed')) + "[tab3_start_predict]")
                return CustomMessageBox(lang['TITLE']['warning'],state['msg'],messagecolor="red",icon="error",parent=self).exec()
            self.mod.resetUsb_value()
            self.set_pause_controls_enabled(True)
            self.change_light('yellowlightid')
            self.monitorSenser = ThreadMonitorSenser(self.mod,self.usbConfig.get('senserid'),self.usbConfig.get('palletsenserid'),self.usbConfig.get('timeout'))
            self.monitorSenser.singal_status.connect(self.status_senser)
            self.monitorSenser.start()
        except Exception as e:
            self.set_pause_controls_enabled(False)
            WriteErrorLogs(str(e) + "[tab3_start_predict]")
            CustomMessageBox(lang['TITLE']['warning'],str(e),messagecolor="red",icon="error",parent=self).exec()
    def status_senser(self,status):
        if not status['status']:
            WriteErrorLogs(str(status.get('msg', 'sensor status failed')) + "[status_senser]")
            return CustomMessageBox(lang['TITLE']['warning'],status['msg'],messagecolor="red",icon="error",parent=self).exec()
        self.inspectTriggerSeq += 1
        if not self.autoInspect:self.autoInspect = True 
        self.tab3_manual_predict(AUTO_INSPECT=True) 
    
    def predict_result(self,result,confidence=0,addList=True,current_item=None):
        try:
            self.confidence = float(self.config_config.get("confidence"))
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            display_result = result
            if result in self.classes:
                if confidence>= self.confidence:
                    color = self.classes.get(result).get('color')
                else:
                    color = self.scorenotmetcolor
                    display_result = "NC"
            else:color = self.ngcolor
            self.label_tab3_result.setText(display_result)
            self.label_tab3_result.setStyleSheet(f"background-color:rgb{tuple(color)};color:#fff")
            if not addList:
                if current_item:current_item.setBackground(QColor(*color))
                return None
            item = QListWidgetItem(timestamp)
            self.label_tab3_result_name.setText(timestamp)
            self.comboBox_tab3_results.setCurrentText(result)
            self.listWidget_tab3_result.insertItem(0,item)
            item.setBackground(QColor(*color))
            # if result not in self.okresult and self.autoInspect: 
            #     self.stop_machine()
            #     self.autoInspect = False
            if (color == self.ngcolor or color == self.scorenotmetcolor) and self.autoInspect:
                self.stop_machine()
                self.autoInspect = False
            return timestamp
        except Exception as e:
            WriteErrorLogs(str(e) + "[predict_result]")
            return timestamp
    def stop_machine(self):
        if self.mod:
            self.btn_tab3_cancleWarn.setVisible(True)
            self.change_light('redlightid')
            if hasattr(self, 'monitorSenser') and self.monitorSenser and self.monitorSenser.isRunning():
                self.monitorSenser.pause(True)
            self.btn_tab3_start.setEnabled(False)
            # self.btn_tab3_manual_predict.setEnabled(False)
            self.btn_tab3_cancleWarn.setStyleSheet("#btn_tab3_cancleWarn{background-color:red}")
    def release_warning(self):
        try:
            self.btn_tab3_cancleWarn.setVisible(False)
            self.mod.setUsb_value(self.usbConfig.get('stopmacineid'),'0')
            self.change_light(None)
            if hasattr(self, 'monitorSenser') and self.monitorSenser:
                if self.monitorSenser.isRunning():
                    self.monitorSenser.pause(False)
                else:
                    self.monitorSenser.start()
            self.mod.setUsb_value(self.usbConfig.get('yellowlightid' if self.pauseDetect else 'greenlightid'),'1')
            self.btn_tab3_start.setEnabled(True)
            # self.btn_tab3_manual_predict.setEnabled(True)
            self.btn_tab3_cancleWarn.setStyleSheet("#btn_tab3_cancleWarn{background-color:#007bc0}")
        except Exception as e:
            WriteErrorLogs(str(e) + "[release_warning]")
            CustomMessageBox(lang['TITLE']['warning'],str(e),messagecolor="red",icon="error",parent=self).exec()
    def set_pix(self,frame,_label):
        try:
            rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)# 将OpenCV的图像格式转换为QImage可以显示的格式
            h, w, ch = rgbImage.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
            px = QPixmap.fromImage(convertToQtFormat)
            _label.setPixmap(px)# 将QImage转换为QPixmap，并显示在QLabel上
            return px
        except Exception as e:
            WriteErrorLogs(str(e) + "[set_pix]")
            return None
class CheckCamera(QThread):
    signal_camera_list = pyqtSignal(list)
    def __init__(self,graph):
        super(CheckCamera, self).__init__()
        self.graph = graph
    def run(self):
        self.graph = FilterGraph()
        devices = self.graph.get_input_devices()
        # self.signal_camera_list.emit(list(reversed(devices)))
        self.signal_camera_list.emit(devices)
class StartCapture(QThread):
    signal_status = pyqtSignal(dict)
    def __init__(self,index):
        super(StartCapture, self).__init__()
        self.index = index
    def run(self):
        try:
            self.cap = cv2.VideoCapture(self.index,cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                WriteErrorLogs(f"cv2.VideoCapture open failed index={self.index}[StartCapture]")
                self.signal_status.emit({"status":False,"msg":lang['MESSAGE']['fail_open_cv']})
            else:
                self.signal_status.emit({"status":True,"data":self.cap})
        except Exception as e:
            WriteErrorLogs(str(e) + "[StartCapture]")
            self.signal_status.emit({"status":False,"msg":str(e)})

class ThreadMonitorSenser(QThread):
    singal_status=pyqtSignal(dict)
    def __init__(self,modbusObject,sensor=0,pallet_senser=1,timeout=1000):
        super().__init__()
        self.modbusObject = modbusObject
        self.sensor = sensor
        self.pallet_senser = pallet_senser
        self.initStrainerSensorStatus = False
        self.timeoutInspect = timeout
        self.tryTimes = 3
        self.secondTryTime = 3
        self.pauseDetect = True
        self._running = True
    def run(self):
        try:
            self._running = True
            while self._running:
                if self.pauseDetect:
                    self.msleep(100)
                    continue
                result = self.modbusObject.getUsb_value(self.pallet_senser)
                if result['status']:
                    if self.tryTimes != 3:self.tryTimes =3
                    data = result['data']
                    if data and not self.initStrainerSensorStatus:
                        self.msleep(int(float(self.timeoutInspect)))
                        result1 = self.modbusObject.getUsb_value(self.pallet_senser)
                        if result1['status']:
                            if self.secondTryTime != 3:self.secondTryTime = 3
                            data1 = result1['data']
                            if not data1:
                                self.msleep(100)
                                continue
                            #如果托盘感应到
                            senserResult = self.modbusObject.getUsb_value(self.sensor)
                            if not senserResult['status']:
                                WriteErrorLogs("child-senserResult:" + senserResult['msg'])
                                self.singal_status.emit({"status":False,"msg":senserResult['msg']})
                                continue
                            senserData = senserResult['data']
                            if not senserData:continue
                            self.initStrainerSensorStatus = True
                            self.singal_status.emit({"status":True,"modstatus":self.initStrainerSensorStatus})
                        else:
                            self.secondTryTime -= 1
                            self.singal_status.emit(result1)
                            if self.secondTryTime == 0:
                                WriteErrorLogs("child-else and try 3 times:" + result1['msg'])
                                self.singal_status.emit({"status":False,"msg":result1['msg']})
                                break
                    elif data==0 and self.initStrainerSensorStatus:#0
                        self.initStrainerSensorStatus = False
                else:
                    self.tryTimes -= 1
                    self.singal_status.emit(result)
                    if self.tryTimes == 0:
                        WriteErrorLogs("main-else and try 3 times:" + result['msg'])
                        self.singal_status.emit({"status":False,"msg":result['msg']})
                        break
                self.msleep(100)
        except Exception as e:
            msg = f"{e}"
            WriteErrorLogs(msg + "[ThreadMonitorSenser]")
            self.singal_status.emit({"status":False,"msg":msg})
            self._running = False
    def pause(self,state):
        self.pauseDetect = state
    def stop(self):
        self._running = False
class ThreadSaveResults(QThread):
    signal_status = pyqtSignal(dict)
    def __init__(self,path,frame,draw_img,timestamp,result,rectify=False,item=None,confidence=0,box=[0,0,0,0]):
        super().__init__()
        self.path = path
        self.frame = frame
        self.draw_img = draw_img
        self.result = result
        self.confidence = confidence
        self.box = box
        self.timestamp = timestamp
    def run(self):
        try:
            str_day = datetime.now().strftime("%Y%m%d")
            raw_img_path = os.path.join(self.path,"02_detection_datasets","source_images")
            raw_json_path = os.path.join(self.path,"02_detection_datasets","source_json")
            detection_results_path = os.path.join(self.path,"01_detection_results",str_day)

            saveResult = SaveJsonImage(f"IMG_{self.timestamp}")
            saveResult.save_image(detection_results_path,self.draw_img) #保存绘制后的检测图片
            #保存csv
            csv_filename = os.path.join(detection_results_path,f"{str_day}.csv")
            file_exists = os.path.exists(csv_filename)
            
            #保存原始图片和json
            saveResult.save_image(raw_img_path,self.frame)
            x1, y1, x2, y2 = self.box
            startPoint,endPoint = (float(x1),float(y1)),(float(x2),float(y2))
            if self.result == "NG":
                os.makedirs(raw_json_path, exist_ok=True)
                empty_json_path = os.path.join(raw_json_path, f"IMG_{self.timestamp}.json")
                with open(empty_json_path, 'w', encoding='utf-8') as file:
                    file.write("{}")
            else:
                saveResult.save_json(raw_json_path,self.result,startPoint,endPoint,self.confidence)
            with open(csv_filename, mode='a', encoding='utf-8', newline='') as f:
                if not file_exists:
                    header = "detection_time,result_text,image_path,result_scores,box\n"
                    f.write(header)
                row = f"{self.timestamp},{self.result},{os.path.join(detection_results_path,f'IMG_{self.timestamp}.jpg')},{self.confidence},{[list(startPoint), list(endPoint)]}\n"
                f.write(row)
            self.signal_status.emit({"status":True})
        except Exception as e:
            msg = f"{e}"
            WriteErrorLogs(msg + "[ThreadSaveResults]")
            self.signal_status.emit({"status":False,"msg":msg})
            self.quit()
            self.wait()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen: QScreen = app.primaryScreen()  # 获取主屏幕对象
    size = screen.size()  # 获取屏幕尺寸（以像素为单位）
    style_file = QFile("static/ui/Layout.qss")
    style_file.open(QFile.ReadOnly | QFile.Text)
    style_stream = QTextStream(style_file)
    app.setStyleSheet(style_stream.readAll())    
    window = Ui_yolo()
    window.showFullScreen()
    sys.exit(app.exec())