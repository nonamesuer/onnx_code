# import argparse
import cv2
import numpy as np
import onnxruntime as ort
# from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession
from Config_Class import ConfigHandler
from Config_Class import WriteErrorLogs
class YOLO11:
    def __init__(self,onnx_model,classes):
        self.onnx_model = onnx_model
        self.classes = classes
        self.classNamesList = list(classes.keys())
        self.config = ConfigHandler().get_all_config('config')
        self.lowerConfidenceName=self.config.get('substitute')
    def load_model(self):
        # 使用 ONNX 模型创建推理会话，自动选择CPU或GPU
        self.session = ort.InferenceSession(
            self.onnx_model, 
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"] if ort.get_device() == "GPU" else ["CPUExecutionProvider"],
        )
        # 获取模型的输入形状
        self.model_inputs = self.session.get_inputs()
        input_shape = self.model_inputs[0].shape  
        self.input_width = input_shape[2]
        self.input_height = input_shape[3]
        # return session
    def preprocess_img(self,input_image):
        """
        对输入图像进行预处理，以便进行推理。
        返回：
            image_data: 经过预处理的图像数据，准备进行推理。
        """
        
        self.img = input_image# 使用 OpenCV 读取输入图像
        self.img_height, self.img_width = self.img.shape[:2]# 获取输入图像的高度和宽度
        img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)# 将图像颜色空间从 BGR 转换为 RGB
        # img = self.img
        # 保持宽高比，进行 letterbox 填充, 使用模型要求的输入尺寸
        img, self.ratio, (self.dw, self.dh) = self.letterbox(img, new_shape=(self.input_width, self.input_height))
        # 通过除以 255.0 来归一化图像数据
        image_data = np.array(img) / 255.0
        # 将图像的通道维度移到第一维
        image_data = np.transpose(image_data, (2, 0, 1))  # 通道优先
        # 扩展图像数据的维度，以匹配模型输入的形状
        image_data = np.expand_dims(image_data, axis=0).astype(np.float32)
        # 返回预处理后的图像数据
        return image_data
    def letterbox(self, img, new_shape=(640, 640), color=(114, 114, 114), auto=False, scaleFill=False, scaleup=True):
        """
        将图像进行 letterbox 填充，保持纵横比不变，并缩放到指定尺寸。
        """
        shape = img.shape[:2]  # 当前图像的宽高
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)
        # 计算缩放比例
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])  # 选择宽高中最小的缩放比
        if not scaleup:  # 仅缩小，不放大
            r = min(r, 1.0)
        # 缩放后的未填充尺寸
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        # 计算需要的填充
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # 计算填充的尺寸
        dw /= 2  # padding 均分
        dh /= 2
        # 缩放图像
        if shape[::-1] != new_unpad:  # 如果当前图像尺寸不等于 new_unpad，则缩放
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        # 为图像添加边框以达到目标尺寸
        top, bottom = int(round(dh)), int(round(dh))
        left, right = int(round(dw)), int(round(dw))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return img, (r, r), (dw, dh)
    def postprocess(self, input_image, output):#这里修改了
        """
        对模型输出进行后处理，以提取边界框、分数和类别 ID。
        参数：
            input_image (numpy.ndarray): 输入图像。
            output (numpy.ndarray): 模型的输出。
        返回：
            numpy.ndarray: 包含检测结果的输入图像。
        """
        # 转置并压缩输出，以匹配预期形状
        outputs = np.transpose(np.squeeze(output[0]))
        rows = outputs.shape[0]
        floatboxes,boxes, scores, class_ids = [],[], [], []
 
        # 计算缩放比例和填充
        # ratio = self.img_width / self.input_width, self.img_height / self.input_height
        # lowerconfidence=float(self.config.get('confidence'))
        lowerlimit=0.5
        try:
            lowerlimit = float(self.config.get('lowerlimit')) if self.config.get('lowerlimit') else 0.5
        except Exception as e:
            WriteErrorLogs(str(e) + "[YOLO11 postprocess lowerlimit]")
        max_score = lowerlimit
        max_index = 0
        max_classes_scores = 0
        for i in range(rows):
            classes_scores = outputs[i][4:]
            max_scores = np.amax(classes_scores)
            if max_scores>max_score:
                max_score=max_scores
                max_index = i
                max_classes_scores = classes_scores
        # print("-------max_score:",max_score,"class_id", np.argmax(max_classes_scores))
        if max_score > lowerlimit:
            # if max_score<lowerconfidence:
            #     class_id=self.classNamesList.index(self.lowerConfidenceName)
            # else:
            class_id = np.argmax(max_classes_scores)
            x, y, w, h = outputs[max_index][0], outputs[max_index][1], outputs[max_index][2], outputs[max_index][3]

            # 将框调整到原始图像尺寸，考虑缩放和填充
            x -= self.dw  # 移除填充
            y -= self.dh
            x /= self.ratio[0]  # 缩放回原图
            y /= self.ratio[1]
            w /= self.ratio[0]
            h /= self.ratio[1]
            f_left= x - w / 2
            f_top = y - h / 2
            left = int(f_left)
            top = int(f_top)
            width = int(w)
            height = int(h)
            floatboxes.append([f_left,f_top,f_left+w,f_top+h])
            boxes.append([left, top, width, height])
            scores.append(max_score)
            class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, scores, lowerlimit, float(self.config.get('iouthres')))
        result = 'NG'
        confidence = None
        floatboxe = [0,0,0,0]
        box = [0,0,0,0]
        score = None
        class_id = None
        for idx in np.array(indices).flatten():
            i = int(idx)
            box = boxes[i]
            floatboxe = floatboxes[i]
            score = scores[i]
            class_id = class_ids[i]
        try:
            if class_id is not None and score is not None:
                result = self.classNamesList[class_id]
                confidence = score
        except Exception as e:
            WriteErrorLogs(str(e) + "[YOLO11 postprocess result_mapping]")
        return input_image,result,confidence,box,floatboxe
    def draw_detections(self, img, box, score, class_name):
        """
        在输入图像上绘制检测到的边界框和标签。
        参数：
            img: 用于绘制检测结果的输入图像。
            box: 检测到的边界框。
            score: 对应的检测分数。
            class_id: 检测到的目标类别 ID。
        
        返回：
            None
        """
        # 提取边界框的坐标
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1.3
        thickness = 3
        x1, y1, w, h = box
        set_confidence = float(self.config.get("confidence", 0.5))
        if score < set_confidence:
            _color = list(map(int,self.config.get("scorenotmetcolor","255,207,0").split(",")))
        else:
            _color = self.classes[class_name]['color']
            # 获取类别对应的颜色
        color = list(reversed(_color))
        # 在图像上绘制边界框
        cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color, thickness)
        score = int(score * 100)
        label = f'score[{class_name}]:{score}'
        # 创建包含类别名和分数的标签文本
 
        # 计算标签文本的尺寸
        (textSizeW, textSizeH), baseline = cv2.getTextSize(label, font, fontScale, thickness)
        margin = 10
        topRight = (img.shape[1] - textSizeW - margin, textSizeH+5)
        
        cv2.putText(img, label, topRight, font, fontScale, color, thickness)
        return img






        # (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
 
        # # 计算标签文本的位置
        # label_x = x1
        # label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10
 
        # # 绘制填充的矩形作为标签文本的背景
        # cv2.rectangle(img, (label_x, label_y - label_height), (label_x + label_width, label_y + label_height), color, cv2.FILLED)
 
        # # 在图像上绘制标签文本
        # cv2.putText(img, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    def predict(self,input_image):
        img_data = self.preprocess_img(input_image)
        outputs = self.session.run(None, {self.model_inputs[0].name: img_data})
        return self.postprocess(self.img, outputs)  # 输出图像
