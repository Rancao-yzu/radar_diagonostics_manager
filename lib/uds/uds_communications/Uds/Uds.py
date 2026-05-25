#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


import queue
import time
from uds.uds_config_tool.IHexFunctions import ihexFile as ihexFileParser
from uds.uds_config_tool.ISOStandard.ISOStandard import IsoDataFormatIdentifier,IsoServices

from uds import Config
from uds.uds_tools import get_data_from_file, crc_check, get_srec_data_from_file
from os import path

import threading

from uds.uds_tools import UdsMessage, ToByteArray
import traceback

import logging

import sys

PROGESSBAR_MARK = "\u200B"

TEST_DLL_PATH = r"E:\code\byd_boot_crc\pythonCode\CRC32.dll"
TEST_WRAPPER_PATH = r"E:\code\byd_boot_crc\pythonCode\pyCrc32.dll"

def show_progress(progress, total, bar_length=50):
    """
    Display a progress bar in the console.
    :param progress: Current progress value.
    :param total: Total progress value.
    :param bar_length: Length of the progress bar in characters.
    """
    percent = (progress / total) * 100  # Calculate the percentage of progress
    status = f"{progress}/{total}"  # Format the progress status
    filled_length = int(bar_length * progress // total)  # Calculate the filled portion of the bar
    bar = '█' * filled_length + '-' * (bar_length - filled_length)  # Construct the progress bar


    # Print the progress bar to the console
    print(f'\r[{bar}] {percent:.2f}% {status}{PROGESSBAR_MARK}', end="")

    # sys.stdout.write(f'\r[{bar}] {percent:.2f}% {status}')
    # sys.stdout.flush()  # Ensure the output is updated immediately

    
##
# @brief a description is needed
class Uds(object):

    ##
    # @brief a constructor
    # @param [in] reqId The request ID used by the UDS connection, defaults to None if not used
    # @param [in] resId The response Id used by the UDS connection, defaults to None if not used
    def __init__(self, iTP, configPath=None, ihexFile=None, **kwargs):

        self.__config = {
            'uds': {
                'transportProtocol': 'CAN',
                'P2_CAN_Client': '1000',
                'P2_CAN_Server': '1000'
            }
        }
        self.__P2_CAN_Client = None
        self.__P2_CAN_Server = None

        self.flashProgressQueue = queue.Queue()

        # self.__loadConfiguration(configPath)
        self.__checkKwargs(**kwargs)

        self.__P2_CAN_Client = float(self.__config['uds']['P2_CAN_Client'])
        self.__P2_CAN_Server = float(self.__config['uds']['P2_CAN_Server'])

        self.tp = iTP

        # used as a semaphore for the tester present
        self.__transmissionActive_flag = False
        #print(("__transmissionActive_flag initialised (clear):",self.__transmissionActive_flag))
        # The above flag should prevent testerPresent operation, but in case of race conditions, this lock prevents actual overlapo in the sending
        self.sendLock = threading.Lock()

        # Process any ihex file that has been associated with the ecu at initialisation
        self.__ihexFile = ihexFileParser(ihexFile) if ihexFile is not None else None
        self.transferData = None


        self._didRead = {
            "SecurityAccessRead": [],
            "CommonRead": [],
        }
        self._secAccess = None

        self._didWakeUp = None

    

    def __loadConfiguration(self, configPath=None):

        baseConfig = path.dirname(__file__) + "\\config.ini"
        self.__config = Config()
        if path.exists(baseConfig):
            self.__config.read(baseConfig)
        else:
            raise FileNotFoundError("No base config file")

        # check the config path
        if configPath is not None:
            if path.exists(configPath):
                self.__config.read(configPath)
            else:
                raise FileNotFoundError("specified config not found")

    def __checkKwargs(self, **kwargs):

        if 'P2_CAN_Server' in kwargs:
            self.__config['uds']['P2_CAN_Server'] = str(kwargs['P2_CAN_Server'])

        if 'P2_CAN_Client' in kwargs:
            self.__config['uds']['P2_CAN_Client'] = str(kwargs['P2_CAN_Client'])


    @property
    def ihexFile(self):
        return self.__ihexFile

    @ihexFile.setter
    def ihexFile(self, value):
        if value is not None:
            self.__ihexFile = ihexFileParser(value)

    
    ##
    # @brief Currently only called from transferFile to transfer ihex files
    def transferIHexFile(self,transmitChunkSize=None,compressionMethod=None):
        if transmitChunkSize is not None:
            self.__ihexFile.transmitChunksize = transmitChunkSize
        if compressionMethod is None:
            compressionMethod = IsoDataFormatIdentifier.noCompressionMethod
        self.requestDownload([compressionMethod], self.__ihexFile.transmitAddress, self.__ihexFile.transmitLength)
        self.transferData(transferBlocks=self.__ihexFile)
        return self.transferExit()
    

    
    def create_msg_blocks(self, data: bytes, transmitChunkSize=510):
        data_len = len(data)
        if data_len == 0:
            return []

        msg_blocks = []

        svc = IsoServices.TransferData
        chunk = transmitChunkSize

        bsc = 1
        for start in range(0, data_len, chunk):
            block = data[start:start + chunk]

            frame = bytearray(2 + len(block))
            frame[0] = svc
            frame[1] = bsc
            frame[2:] = block

            msg_blocks.append(frame)

            bsc += 1
            if bsc == 0x100:
                bsc = 0x00

        return msg_blocks

    
    def send_app_data(self, msg_blocks: list, intconfig = None, startIndex = 0, sendBlockCount = None, progress_callback = show_progress):
        reqService = IsoServices.TransferData + 0x40
        
        if progress_callback is None:
            progress_callback = show_progress

        if sendBlockCount == None:
            sendBlockCount = len(msg_blocks)

        # calculate the number of blocks to send
        totalLen = min(sendBlockCount, len(msg_blocks) - startIndex)

        # get the blocks to send
        new_msg_blocks = msg_blocks[startIndex : startIndex+totalLen]

        new_totalLen = len(new_msg_blocks)

        if intconfig is not None:

            intconfig["intManager"].update_variable(intconfig['intMap'].get("progress"),[0,new_totalLen])

        for idx,msg in enumerate(new_msg_blocks):

            # # back to the line start
            # print('\r', end="")
            # # print status bar
            # print(f" Sending block {idx+1}/{totalLen}", end="")

            self.tp.send(msg)

            res = self.tp.recv(block=True, timeout=1.0)
            if res is None:
                logging.error("No response received during data transfer")
                return False, 1
                # raise Exception("No response received during data transfer")
            # print(*[format(i, '02x') for i in res])
            # while res == [0x7f, 0x36, 0x78]:
            while res == bytearray([0x7f, 0x36, 0x78]):
                # print("service in progress")
                # time.sleep(0.001)
                # try:
                    # time.sleep(0.001)
                    res = self.tp.recv(block=True, timeout=1.0)
                    if res is None:
                        logging.error("No response received during data transfer")
                        return False, 2
                        # raise Exception("No response received during data transfer")
                    # print(res)
                # except Exception as e:
                #     # errorStr = str(e)
                #     print(res, e)
                #     if res != [0x7f, 0x36, 0x78]:
                #         raise e
                # finally:
                #     time.sleep(0.001)

            # print('transfer recv: ', *[format(i, '02x') for i in res])
            if res == bytearray([reqService,(idx+1)%0x100]):
                # print(f" success", end="")
            
                # if intconfig is not None:
                #     intconfig["intManager"].update_variable(intconfig['intMap'].get("progress"),[idx+1,new_totalLen])

                # print(" success", end="")
                # print(f"{PROGESSBAR_MARK} {idx+1}/{totalLen}", end="\r")
                progress_callback(idx+1, new_totalLen)

            else:
                
                print(f"\n {[format(i, '02x') for i in res]} failed last packet:")
                print(*[format(i, '02x') for i in msg])
                print(f"msg length: {len(msg)}, response length: {len(res)}")
                # clear line
                return False, 3
            
                
            
        print("\n")


        return True, None
    

    def loadFile(self, fileName, transmitChunkSize, crcType="CRC32", crcCheckStartAddr=0):
        # To do - how to make compatible with the old testprj version
        self.transmitChunkSize = transmitChunkSize

        if fileName is None and self.__ihexFile is None:
                raise ValueError("file to transfer has not been specified")
        if fileName.endswith('.s19'):
            binAddr, binData = get_srec_data_from_file(fileName)
        elif fileName.endswith('.hex'):
            binAddr, binData = get_data_from_file(fileName, 0)
        else:
            raise ValueError(f"{fileName} is not a supported file type")
        binLen = [len(binData) >> 8*i & 0xFF for i in range(3,-1,-1)]
        binAddr = [binAddr >> 8*i & 0xFF for i in range(3,-1,-1)]

        
        # msg_blocks = self.create_msg_blocks(binData, transmitChunkSize)

        # the crc check should not contain some of the data, so we need to check if the crcStartAddr is set
        if crcCheckStartAddr != 0:
            crcCheckBinData = binData[crcCheckStartAddr:]
        else:
            crcCheckBinData = binData
        

        # crc = crc_check(crcCheckBinData, type=crcType, dll_path=TEST_DLL_PATH, warpper_path=TEST_WRAPPER_PATH)
        # crc = [crc >> 8*i & 0xFF for i in range(3,-1,-1)]
        self.transferData = {'data':binData, 'totalLen':binLen, 'address':binAddr, 'crc':0}

    def getFileInfo(self):
        if self.transferData is None:
            raise Exception("No file loaded for transfer")
        return self.transferData


    def transferFile(self,fileData, 
                     fileStartAddr = 0, 
                     fileSize = 1, 
                     startIndex = 0,
                     sendBlockCount = None, 
                     intconfig = None, 
                     progress_callback = None,
                     compressionMethod=0x00, 
                     chunkSize=None):
        # if self.transferData is None:
        #     raise Exception("No file loaded for transfer")


        # msg = UdsMessage()
        # msg.create(IsoServices.RequestDownload, [compressionMethod ,0x44 ,fileStartAddr, fileSize])
        # res = self.send(msg)
        # print(' request download ', 'success' if res[0] else 'failed')
        # if res[0] == False:
        #     return False

        if chunkSize is not None:
            self.transmitChunkSize = chunkSize

        msg_blocks = self.create_msg_blocks(fileData, self.transmitChunkSize)

        res = self.send_app_data(msg_blocks, intconfig, startIndex, sendBlockCount, progress_callback)

        # msg.create(IsoServices.RequestTransferExit)
        # # stop transfer
        # if res == True:
        #     res = self.send(msg )
        #     print(' stop transfer ', 'success' if res[0] else 'failed')

        return res

   
    # ##
    # # @brief This will eventually support more than one file type, but for now is limited to ihex only
    # def transferFile(self, Res = {'flashRes': True}, compressionMethod=0x00):
    #     try:
    #         if self.transferData is None:
    #             raise Exception("No file loaded for transfer")


    #         msg = UdsMessage()
    #         msg.create(IsoServices.RequestDownload, [compressionMethod ,0x44 ,self.transferData['address'], self.transferData['totalLen']])
    #         res = self.send(msg)
    #         print(' request download ', res[0])
    #         if res[0] == False:
    #             return False


    #         res = self.send_app_data(self.transferData['data'])

    #         # if (self.transferData['address'] != 402653184):
    #         msg.create(IsoServices.TesterPresent, [0x80])
    #         self.send(msg, functionalReq=True)
    #         self.send(msg, functionalReq=True)
    #         self.send(msg, functionalReq=True)
    #         self.send(msg, functionalReq=True)
    #         self.send(msg, functionalReq=True)
    #         self.send(msg, functionalReq=True)


    #         msg.create(IsoServices.RequestTransferExit)
    #         # stop transfer
    #         if res == True:
    #            res = self.send(msg )
    #         #    print(' stop transfer ', res[1], end=" | ")
               



    #         return res
    #     except Exception as e:
    #         traceback.print_exc()
    #         Res['flashRes'] = False
    #         print('transferFile  ',e)


    def sercurityAccess(self, seedLevel:int, dllPath:str, seedFunc=None, printLog = False):
        if seedFunc is None:
            return False, None
        keyLevel = seedLevel + 1
        msg = UdsMessage()
        msg.create(IsoServices.SecurityAccess, [seedLevel])
        res = self.send(msg)
        if printLog:
            print(' security access ', "")
        time.sleep(0.1)

        if res[0] == True:
            seed = res[1].frame[2:]
            if printLog:
                print(" Seed: ", *[format(i, '02x') for i in seed], end=" | ")
            key = seedFunc(dllPath, seed, seedLevel)
            
            if key is None:
                res = False
            if res:
                if printLog:
                    print(" Key generated:", *[format(i, '02x') for i in key], end=" | ")
                msg.create(IsoServices.SecurityAccess, [keyLevel, key])
                res = self.send(msg)
                return res
            else:
                return False, None
        else:
            return False, res[1]


    ##
    # @brief
    def send(self, requestUdsMsg:UdsMessage, responseRequired=True, timeout=1.0, confirm=[], PrintLog=False):
        # sets a current transmission in progress - tester present (if running) will not send if this flag is set to true
        # self.tp.clear_rx_queue()

        res =True
        
        retryCount = 10
        self.__transmissionActive_flag = True
        #print(("__transmissionActive_flag set:",self.__transmissionActive_flag))

        respUdsMsg = UdsMessage()

        # We're moving to threaded operation, so putting a lock around the send operation. 
        self.sendLock.acquire()
        if PrintLog:
            print(" request:",*[format(i, '02x') for i in requestUdsMsg.frame], end=" | ")
        payload = requestUdsMsg.frame
        
        try:
            a = self.tp.send(payload)
        finally:
            self.sendLock.release()



        # Note: in automated mode (unlikely to be used any other way), there is no response from tester present, so threading is not an issue here.
            
        if responseRequired:
            try:
                
                respUdsMsg.frame = self.tp.recv(block=True, timeout=timeout)
                res = True
                
                if len(respUdsMsg.frame) == 0:
                    res = False
                    raise Exception("no response received")
            except Exception as e:
                if PrintLog:
                    print(traceback.format_exc())
                errorStr = str(e)
                res = False

            if res == False:
                if PrintLog:
                    print(errorStr, end=" | ")
                return res,2

            # if the response indicates that the device still working on the request, keep checking until a final response is received

            # xx ff 78 is bad response from the device - not a valid wait response
            # if len(respUdsMsg.frame) > 2 and respUdsMsg.frame[1] == 0xFF and respUdsMsg.frame[2] ==  0x78:
            #     res = False
            #     print(" error response: ",*[format(i, '02x') for i in respUdsMsg.frame], end=" | ")
            #     return res,respUdsMsg

            # print( [format(i,'02x') for i in respUdsMsg.frame])
            
            try:
                while (len(respUdsMsg.frame) > 2 and respUdsMsg.frame[2] == 0x78
                ):
                    time.sleep(0.5)
                    if PrintLog:
                        print(f"service in progress {' '.join([format(i, '02x') for i in respUdsMsg.frame])}")

                    try:
                        res = self.tp.recv(block=True, timeout=10.0)
                        # ✅ 空响应 = ECU还没准备好，不报错，直接继续
                        if not res:
                            
                            # retryCount -= 1
                            # if retryCount == 0:
                                # res = False
                                # break
                            # continue
                            return res,2

                        # ✅ 有响应则更新 UDS 消息帧
                        respUdsMsg.frame = bytearray(res)

                    except Exception as e:
                        if PrintLog:
                            print(traceback.format_exc())
                            print(e)
                        retryCount -= 1
                        if retryCount == 0:
                            res = False
                            break
                        continue

                if len(confirm) > 0:
                    confirm = bytearray(confirm)
                    checkData = respUdsMsg.frame[1:]
                    if PrintLog:
                        print(" confirm: ",*[format(i, '02x') for i in confirm], end=" | ")
                        print(" checkData: ",*[format(i, '02x') for i in checkData], end=" | ")
                    for idx in range(len(confirm)):
                        if checkData[idx] != confirm[idx]:
                            res = False
                            if PrintLog:
                                print(" error response: ",*[format(i, '02x') for i in respUdsMsg.frame], end=" | ")
                            return res,3

                else: 
                    if len(respUdsMsg.frame) > 1 and respUdsMsg.frame[0] == 0x7F:
                        if PrintLog:
                            print(" error response: ",*[format(i, '02x') for i in respUdsMsg.frame], end=" | ")
                        res = False
                        return res,3

                if PrintLog:
                    print(" response: ",*[format(i, '02x') for i in respUdsMsg.frame])

            except Exception as e:
                if PrintLog:
                    print(traceback.format_exc())
                    print(e, end=" | ")
                res = False
                return res,4

            
        # Lets go of the hold on transmissions - allows test present to resume operation (if it's running)
        self.__transmissionActive_flag = False
        #print(("__transmissionActive_flag cleared:",self.__transmissionActive_flag))

        
        return res,respUdsMsg


    def disconnect(self):

        self.tp.closeConnection()

    def getDeviceDID(self, did:bytes):
        msg = UdsMessage()
        msg.create(IsoServices.ReadDataByIdentifier, [did])
        try:
            for i in range(3):
                res = self.send(msg, responseRequired=True, functionalReq=False, timeout=200)
                print(res[0])
                if res[0] == True:
                    return res[1].frame[2:]
                else:
                    # print(f"Read DID {did} failed, retrying {i+1}")
                    pass
                    # raise Exception(f"Read DID {did} failed")
        except Exception as e:
            return None
        
    def readAllDID(self):
        resList = []


        # print("\n\n\nDIDWakeUp ", self._didWakeUp)
        if self._didWakeUp is not None and self._didWakeUp == True:
            for i in range(5):
                self.tp.wakeup()
                time.sleep(0.2)

            
        for didInfo in self._didRead['CommonRead']:
            res = self.getDeviceDID(didInfo.did)
            resList.append({
                "did": didInfo.did,
                "name": didInfo.name,
                "data": didInfo.decode(res)
            })
            time.sleep(0.05)
        for didInfo in self._didRead['SecurityAccessRead']:
            # if self._secAccess is None:
            #     resSercurityAccess = self.sercurityAccess(
            #         seedLevel=self._secAccess.seedLevel,
            #         keyLevel=self._secAccess.keyLevel,
            #         dllPath=self._secAccess.dllPath,
            #         seedFunc=self._secAccess.seedFunc
            #     )
            #     if resSercurityAccess[0] == False:
            #         raise Exception("Security access failed")
            # else:
            #     raise ValueError("No security access object specified")
            res = self.getDeviceDID(didInfo.did)
            resList.append({
                "did": didInfo.did,
                "name": didInfo.name,
                "data": didInfo.decode(res)
            })
            time.sleep(0.05)
        return resList
    
    def setSecurityAccess(self, seedLevel:int, keyLevel:bytes, dllPath:str, seedFunc=None):
        if seedFunc is None:
            raise ValueError("No seed function specified")
        self._secAccess = SecurityAccess(seedLevel=seedLevel, keyLevel=keyLevel, dllPath=dllPath, seedFunc=seedFunc)
        
    def setDidList(self, didInfoObj:list,):
        didRead = {
            "SecurityAccessRead": [],
            "CommonRead": [],
        }
        infoList = didInfoObj["infoList"]

        for didInfo in infoList:
            didreadObj = DidRead(**didInfo)
            # if didInfo['securityAccess'] == True:
            #     didRead["SecurityAccessRead"].append(didreadObj)
            # else:
                # didRead["CommonRead"].append(didreadObj)
            didRead["CommonRead"].append(didreadObj)
        self._didRead = didRead
        self._didWakeUp = didInfoObj["wakeup"]
        return didRead
        
    ##
    # @brief
    def isTransmitting(self):
        #print(("requesting __transmissionActive_flag:",self.__transmissionActive_flag))
        return self.__transmissionActive_flag
    
class DidRead(object):
    def __init__(self, did, name, dataType, securityAccess = None):
        if type(did) == str:
            did = int(did, 16)
        self.did = did
        self.name = name
        self.dataType = dataType
        self.securityAccess = securityAccess

    def decode(self, data):
        if data is None:
            return 'NA'
        if self.dataType == 'ASCII':
            return bytes(data).decode('ascii', errors='ignore')
        elif self.dataType == 'BCD':
            return self.decode_BCD(data)
        elif self.dataType == 'HEX':
            dataString = " ".join([format(i, '02x') for i in data])
            return dataString
        elif self.dataType == 'NUM':
            return int.from_bytes(data, byteorder='big')

    def decode_BCD(self, data):
        decimal = 0
        for byte in data:
            # 拆分每个字节的高4位和低4位
            high = (byte >> 4) & 0x0F  # 高4位
            low = byte & 0x0F  # 低4位
            decimal = decimal * 100 + high * 10 + low
        return str(decimal)

    def __repr__(self):
        return f"DidRead(did={self.did}, name={self.name}, securityAccess={self.securityAccess})"
    
class SecurityAccess(object):
    def __init__(self, seedLevel:int, keyLevel:bytes, dllPath:str, seedFunc=None):
        self.seedLevel = seedLevel
        self.keyLevel = keyLevel
        self.dllPath = dllPath
        if seedFunc is None:
            raise ValueError("No seed function specified")
        self.seedFunc = seedFunc

    def __repr__(self):
        return f"SecurityAccess(seedLevel={self.seedLevel}, keyLevel={self.keyLevel}, dllPath={self.dllPath}, seedFunc={self.seedFunc})"


if __name__ == "__main__":

    pass
