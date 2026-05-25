
# from .ISOStandard import IsoServices as SID
from .UdsHandler import serviceHandler

from enum import IntEnum
class SID(IntEnum):

    DiagnosticSessionControl = 0x10
    EcuReset = 0x11
    ClearDiagnosticInformation = 0x14
    ReadDTCInformation = 0x19
    ReadDataByIdentifier = 0x22
    ReadMemoryByAddress = 0x23
    ReadScalingDataByIdentifier = 0x24
    SecurityAccess = 0x27
    CommunicationControl = 0x28
    ReadDataByPeriodicIdentifier = 0x2A
    DynamicallyDefineDataIdentifier = 0x2C
    WriteDataByIdentifier = 0x2E
    InputOutputControlByIdentifier = 0x2F
    RoutineControl = 0x31
    RequestDownload = 0x34
    RequestUpload = 0x35
    TransferData = 0x36
    RequestTransferExit = 0x37
    TesterPresent = 0x3E
    WriteMemoryByAddress = 0x3D
    AccessTimingParameter = 0x83
    SecuredDataTransmission = 0x84
    ControlDTCSetting = 0x85
    ResponseOnEvent = 0x86
    LinkControl = 0x87
    
RESPONSE_OFFSET = 0x40


def isInUdsList(id):
    """
    Checks if an ID is in the UDS list
    """
    return id in SID._value2member_map_

def findUdsServiceName(id):
    """
    Finds the name of a UDS service given its ID.
    :param id: The service ID.
    :return: The name of the service.
    """
    return SID(id).name

def ToByteArray(*args):
    """
    Converts a list of integers (and nested lists/tuples) to a byte array.
    Handles both single-byte and multi-byte integers.
    """
    stack = list(args)
    result = []
    while stack:
        item = stack.pop(0)
        if isinstance(item, (bytearray)):
            result += item
        elif isinstance(item, (tuple, list, bytes)):
            stack = list(item) + stack
        elif isinstance(item, int):
            if item < 0:
                raise ValueError("Negative values are not allowed")
            if item <= 0xff:
                result.append(item)
            else:
                byte_length = (item.bit_length() + 7) // 8
                for i in range(byte_length - 1, -1, -1):
                    result.append((item >> (8 * i)) & 0xFF)
        else:
            raise TypeError("Unsupported type")

    return result



class UdsMessage():
    def __init__(self, maxMsgSize=4095):
        self.service = None
        self.param = None
        self.serviceName = None
        self.maxMsgSize = maxMsgSize
        self.msg = []

    def __str__(self):
        if len(self.msg) == 0:
            return "None"
        return '0x' + ' 0x'.join([format(i, "02x") for i in self.msg])



    def create(self, service, *args):
        """
        Creates a UDS message.
        :param service: The service ID.
        :param args: Parameters for the message.
        """
        self.service = service
        self.param = args
        self.msg = ToByteArray(service, *args)
        if len(self.msg) > self.maxMsgSize:
            raise ValueError(f"exceeds maximum size: {len(self.msg)} > {self.maxMsgSize}")
        return self.msg


    
    def unpack(self):
        """
        Unpacks a UDS message into its constituent parts.
        :param msg: The message to unpack.
        :return: A tuple containing the service ID and parameters, or None if invalid.
        """

        if len(self.msg) > self.maxMsgSize:
            raise ValueError(f"exceeds maximum size: {len(self.msg)} > {self.maxMsgSize}")

        if len(self.msg) < 2:
            return None

        self.service = self.msg[0] 
        
        if not isInUdsList(self.service - RESPONSE_OFFSET):
            return None
        
        self.serviceName = findUdsServiceName(self.service - RESPONSE_OFFSET)
        self.param = self.msg[1:]

        return (self.serviceName, self.service), self.param

    @property
    def frame(self):
        """ Returns the current message frame. """
        # return self.msg[:] if self.msg else None
        return self.msg
    
    @frame.setter
    def frame(self, msg):
        """ Sets a new message frame. """
        if msg is None:
            self.msg = []
            return
        
        if len(msg) > self.maxMsgSize:
            raise ValueError(f"exceeds maximum size: {len(msg)} > {self.maxMsgSize}")

        self.msg = msg
        self.service = self.msg[0] 


    
    
def handleUdsResponse(udsMsg:UdsMessage, serviceHandler: dict):
    """
    Handles a UDS message
    """
    service, param = udsMsg.unpack()

    if service is not None:
        serviceName = service[0]
    else:
        serviceName = 'Unknown'
    
    if service[1] in serviceHandler:
        serviceHandler[service[1]](param)
    else:
        raise ValueError(f"Unsupported service: {serviceName}")



if __name__ == "__main__":
    sendMsg = UdsMessage()
    print(sendMsg.frame)
    print(sendMsg.create(SID.DiagnosticSessionControl, 0x01, (0x02, [0x03,0x04]), [0x05, 0x06]))
    print(sendMsg.frame)
    print(sendMsg.create(0x50, [0x05, 0x06]))

    

    recvMsg = UdsMessage()
    recvMsg.frame = sendMsg.frame
    print(recvMsg.unpack())

    handleUdsResponse(recvMsg, serviceHandler)
    


