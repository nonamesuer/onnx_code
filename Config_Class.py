from configparser import ConfigParser,NoSectionError,NoOptionError
from datetime import datetime
import json,os,time,cv2,shutil
def WriteErrorLogs(data,file_path="log/",file="Error.log",nowStr=None,max_row=10000):
    """日志(默认最大10000行)

    Args:
        data (str): 需要写入的内容
        file_path (str, optional): _description_. Defaults to "".
        file (str, optional): _description_. Defaults to "Error.log".
        nowStr (str, optional): _description_. Defaults to now.
        max_row (int, optional): _description_. Defaults to 500.
    """
    fileName = file_path + file
    if not nowStr:
        nowtime = datetime.now()
        nowStr = nowtime.strftime('%Y/%m/%d %H:%M:%S')
    data = str(nowStr) + " | " + str(data) + "\n"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    # 写入新数据
    with open(fileName, 'a', encoding='utf-8') as file:
        file.write(data)
    # 读取文件内容，计算行数
    with open(fileName, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        num_lines = len(lines)
    # 如果行数超过500，删除最早的数据
    if num_lines > 500:
        with open(fileName, 'w', encoding='utf-8') as file:
            file.writelines(lines[num_lines - max_row:])
class ConfigHandler(ConfigParser):
    def __init__(self,path='config.ini', encoding='utf-8'):
        super().__init__(inline_comment_prefixes="#")
        self.path = path
        self.encoding = encoding
        self.read(path, encoding=encoding)

    def get_sin_config(self,part,key):
        """获取单一配置

        Args:
            part (str): 主名称
            key (str): 子名称

        Returns:
            str: 子值
        """
        try:
            value = super().get(part,key)
            return value
        except NoSectionError:
            WriteErrorLogs(f"Section {part} not found in the config file.")
            return None
        except NoOptionError:
            WriteErrorLogs(f"Option {key} not found in section {part}.")
            return None
    def get_all_config(self,part):
        """获取部分配置

        Args:
            part (str): 主名称

        Returns:
            dict: 部分值
        """
        try:
            value = super().items(part)
            return dict(value)  # 将items返回的元组列表转换为字典
        except NoSectionError:
            WriteErrorLogs(f"Section {part} not found in the config file.")
            return None
    def set_config(self, part, key, value):
        """设置配置

        Args:
            part (str): 主名称
            key (str): 子名称
            value (str): 设置值

        Returns:
            bool: ...
        """
        try:
            if not self.has_section(part):
                self.add_section(part)
            self.set(part, key, value)
            with open(self.path, 'w', encoding=self.encoding) as f:
                self.write(f)
            return True
        except Exception as e:
            WriteErrorLogs(f"An error occurred: {e}")
            return False
class JsonFile(object):
    def __init__(self, file_path):
        self.file =file_path
        if not os.path.exists(self.file):
            with open(self.file,'w') as file:
                pass
    def read_json_file(self):
        with open(self.file,'r',encoding="utf-8") as file:
            json_str = file.read()
        if json_str == "":
            self.write_json_file({})
            return {}
        data = json.loads(json_str)
        return data
    def write_json_file(self,cache_data):
        while True:
            try:
                with open(self.file, 'w', encoding='utf-8') as file:
                    json.dump(cache_data, file, indent=4, ensure_ascii=False)
                break
            except PermissionError:
                # 如果文件被锁定，等待并重试
                time.sleep(0.5)
con_obj = ConfigHandler()
con_lang = con_obj.get_sin_config("Lang","language")
lang = JsonFile(f'static/lang/{con_lang}.json').read_json_file()
def is_path_accessible(path):
    """
    检查给定的路径是否可以正常访问。
    
    参数:
    path (str): 要检查的路径。
    
    返回:
    bool: 如果路径可以访问，则返回 True；否则返回 False。
    """
    try:
        return True if os.access(path, os.F_OK) else False
    except:
        return False
class SaveJsonImage():
    def __init__(self,filename):
        self.fileName = filename
    def write_json_file(self,path,cache_data):
        # with open(self.file, 'w',encoding='utf-8') as file:
        #     json.dump(cache_data, file, indent=4)
        while True:
            try:
                with open(path, 'w', encoding='utf-8') as file:
                    json.dump(cache_data, file, indent=4, ensure_ascii=False)
                break
            except PermissionError:
                # 如果文件被锁定，等待并重试
                time.sleep(0.5)
    def save_json(self,path:str,label:str,start_point:tuple,end_point:tuple,confidence):
        data = {
            "version": "5.5.0",
            "flags": {},
            "confidence":str(confidence),
            "shapes": [
                {
                    "label": label,
                    "points": [
                        [float(start_point[0]), float(start_point[1])],
                        [float(end_point[0]), float(end_point[1])]
                    ],
                    "group_id": None,
                    "description": "",
                    "shape_type": "rectangle",
                    "flags": {},
                    "mask": None
                }
            ]
        }
        os.makedirs(path, exist_ok=True)
        filepath = rf"{path}/{self.fileName}.json"
        # 保存JSON文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    def save_image(self,path,frame):
        os.makedirs(path,exist_ok=True)
        filepath = rf"{path}/{self.fileName}.jpg"
        cv2.imwrite(filepath, frame)
    def save_txt(self):
        """_summary_:已弃用
        """
        
        self.configPath = ConfigHandler().get_all_config('Path')
        predictTxtPath = self.configPath.get('predictlabelpath')
        predictImgPath = self.configPath.get('predictimgpath')

        sourcepredictlabelpath = self.configPath.get('sourcepredictlabelpath')
        sourcerectifylabelpath = self.configPath.get('sourcerectifylabelpath')
        sourcepredictimgpath = self.configPath.get('sourcepredictimgpath')
        sourcerectifyimgpath = self.configPath.get('sourcerectifyimgpath')
        os.makedirs(predictTxtPath, exist_ok=True)
        os.makedirs(predictImgPath, exist_ok=True)
        self.configJson = JsonFile("static/config/labels.json").read_json_file()
        self.classes = self.configJson.get('cylinder')
        self.classNames = list(self.classes.keys())
        self.convert_jsonTotxt(sourcepredictlabelpath,predictTxtPath,sourcepredictimgpath,predictImgPath)
        self.convert_jsonTotxt(sourcerectifylabelpath,predictTxtPath,sourcerectifyimgpath,predictImgPath)
        # self.clear_folder((sourcepredictlabelpath,sourcerectifylabelpath,sourcepredictimgpath,sourcerectifyimgpath))
    def convert_jsonTotxt(self,jsonPath,txtPath,oldPicturePath,newPicturePath):
        os.makedirs(txtPath,exist_ok=True)
        os.makedirs(newPicturePath,exist_ok=True)
        for filename in os.listdir(jsonPath):
            if filename.endswith(".json"):
                json_path = os.path.join(jsonPath, filename)
                jaon_label = JsonFile(json_path).read_json_file()
                pictureName = f"{filename[:-5]}.jpg"
                oldPicture = f"{oldPicturePath}/{pictureName}"
                if not os.path.isfile(oldPicture):
                    continue
                yolo_annotations = []
                for shape in jaon_label['shapes']:
                    label = shape['label']
                    if label not in self.classNames:
                        break
                    class_id = self.classNames.index(label)
                    points = shape['points']
                    if shape['shape_type'] == 'rectangle':
                        (x1, y1), (x2, y2) = points
                    else:
                        break
                    x_center = (x1 + x2) / 2.0 / 640
                    y_center = (y1 + y2) / 2.0 / 640
                    width = (x2 - x1) / 640
                    height = (y2 - y1) / 640
                    yolo_annotations.append(f"{class_id} {x_center} {y_center} {width} {height}")
                newPicture = f"{newPicturePath}/{pictureName}"
                shutil.move(oldPicture, newPicture)
                output_file = os.path.join(txtPath, os.path.splitext(os.path.basename(json_path))[0] + '.txt')
                with open(output_file, 'w') as f:
                    f.write('\n'.join(yolo_annotations))
    def clear_folder(self,folder_paths:tuple):
        for folder_path in folder_paths:
            shutil.rmtree(folder_path, ignore_errors=True)
            # 重新创建空文件夹
            os.makedirs(folder_path, exist_ok=True)

