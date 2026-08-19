import ctypes
import ctypes.wintypes
import cdio
from Config_Class import WriteErrorLogs
class UsbDio:
    def __init__(self,usbConfig):
        self.usbConfig = usbConfig
        self.dev_name = self.usbConfig.get('devicename')
        #初始变量
        self.err_str = ctypes.create_string_buffer(256)
        self.dio_id = ctypes.c_short()
        self.io_data = ctypes.c_ubyte()
        self.lret = cdio.DioInit(self.dev_name.encode(), ctypes.byref(self.dio_id))
        self.usage_outputnum = None
    def inital_device(self):
        if self.lret != cdio.DIO_ERR_SUCCESS:
            cdio.DioGetErrorString(self.lret, self.err_str)
            return {"status":False,"msg":f"usb connect failed-DioInit = {self.lret}: {self.err_str.value.decode('sjis')}"}
        return {"status":True}
    def isnum(self,str, base):
        """验证是否是整数"""
        try:
            if 16 == base:
                int(str, 16)
            else:
                int(str)
        except:
            return False
        return True
    def setUsb_value(self,bit_num,value):
        #检测点位是否合法
        if not self.isnum(bit_num, 10):return {"status":False,"msg":f"set usb-dio point format is error(actual:{bit_num},need:number or 'number')"}
        if not self.isnum(value,16):return {"status":False,"msg":f"set usb-dio setValue format is error(actual:{value},need:str-'number')"}
        #实际逻辑
        while True:
            bit_no = ctypes.c_short(int(bit_num))
            io_data = ctypes.c_ubyte(int(value, 16))

            lret = cdio.DioOutBit(self.dio_id, bit_no, io_data)
            if lret == cdio.DIO_ERR_SUCCESS:
                cdio.DioGetErrorString(lret, self.err_str)
                return {"status":True}
            else:
                cdio.DioGetErrorString(lret, self.err_str)
                return {"status":False,"msg":f"set use-dio failed (DioOutpBit = {lret}: {self.err_str.value.decode('sjis')})"}
    def getUsb_value(self,bit_num):
        #检测点位是否合法
        if not self.isnum(bit_num, 10):return {"status":False,"msg":f"get usb-dio point format is error(actual:{bit_num},need:number or 'number')"}
        #实际逻辑
        bit_no = ctypes.c_short(int(bit_num))
        lret = cdio.DioInpBit(self.dio_id, bit_no, ctypes.byref(self.io_data))
        if lret == cdio.DIO_ERR_SUCCESS:
            cdio.DioGetErrorString(lret, self.err_str)
            # return {"status":True,"data":int(self.io_data.decode('utf-8'))}
            return {"status":True,"data":int(self.io_data.value)}
        else:
            cdio.DioGetErrorString(lret, self.err_str)
            return {"status":False,"msg":f"get use-dio failed (DioOutpBit = {lret}: {self.err_str.value.decode('sjis')}"}
    def resetUsb_value(self):
        if not self.usage_outputnum:self.usage_outputnum = self.usbConfig.get('outputnum')
        if not self.usage_outputnum:return
        try:
            for num in range(int(self.usage_outputnum)):
                self.setUsb_value(str(num),'0')
        except Exception as e:
            WriteErrorLogs(str(e) + "[UsbDio resetUsb_value]")
            return