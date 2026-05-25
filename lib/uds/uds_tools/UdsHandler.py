from .ISOStandard import IsoServices as SID, RESPONSE_OFFSET


def handleDiagnosticSessionControl(udsParam):
    """
    Handles a Diagnostic Session Control request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleEcuReset(udsParam):
    """
    Handles an ECU Reset request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleReadDataByIdentifier(udsParam):
    """
    Handles a Read Data By Identifier request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleClearDiagnosticInformation(udsParam):
    """
    Handles a Clear Diagnostic Information request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleReadDTCInformation(udsParam):
    """
    Handles a Read DTC Information request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleWriteDataByIdentifier(udsParam):
    """
    Handles a Write Data By Identifier request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleReadMemoryByAddress(udsParam):
    """
    Handles a Read Memory By Address request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleReadScalingDataByIdentifier(udsParam):
    """
    Handles a Read Scaling Data By Identifier request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleSecurityAccess(udsParam):
    """
    Handles a Security Access request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleCommunicationControl(udsParam):
    """
    Handles a Communication Control request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleReadDataByPeriodicIdentifier(udsParam):
    """
    Handles a Read Data By Periodic Identifier request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleDynamicallyDefineDataIdentifier(udsParam):
    """
    Handles a Dynamically Define Data Identifier request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleInputOutputControlByIdentifier(udsParam):
    """
    Handles an Input Output Control By Identifier request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleRoutineControl(udsParam):
    """
    Handles a Routine Control request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleRequestDownload(udsParam):
    """
    Handles a Request Download request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleRequestUpload(udsParam):
    """
    Handles a Request Upload request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleTransferData(udsParam):
    """
    Handles a Transfer Data request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleRequestTransferExit(udsParam):
    """
    Handles a Request Transfer Exit request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleTesterPresent(udsParam):
    """
    Handles a Tester Present request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleWriteMemoryByAddress(udsParam):
    """
    Handles a Write Memory By Address request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleAccessTimingParameter(udsParam):
    """
    Handles an Access Timing Parameter request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleSecuredDataTransmission(udsParam):
    """
    Handles a Secured Data Transmission request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleControlDTCSetting(udsParam):
    """
    Handles a Control DTC Setting request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleResponseOnEvent(udsParam):
    """
    Handles a Response On Event request
    """
    if len(udsParam)  == 0:
        return None
    pass


def handleLinkControl(udsParam):
    """
    Handles a Link Control request
    """
    if len(udsParam)  == 0:
        return None
    pass


serviceHandler = {
    SID.DiagnosticSessionControl + RESPONSE_OFFSET: handleDiagnosticSessionControl,
    SID.EcuReset + RESPONSE_OFFSET: handleEcuReset,
    SID.ReadDataByIdentifier + RESPONSE_OFFSET: handleReadDataByIdentifier,
    SID.ClearDiagnosticInformation + RESPONSE_OFFSET: handleClearDiagnosticInformation,
    SID.ReadDTCInformation + RESPONSE_OFFSET: handleReadDTCInformation,
    SID.WriteDataByIdentifier + RESPONSE_OFFSET: handleWriteDataByIdentifier,
    SID.ReadMemoryByAddress + RESPONSE_OFFSET: handleReadMemoryByAddress,
    SID.ReadScalingDataByIdentifier + RESPONSE_OFFSET: handleReadScalingDataByIdentifier,
    SID.SecurityAccess + RESPONSE_OFFSET: handleSecurityAccess,
    SID.CommunicationControl + RESPONSE_OFFSET: handleCommunicationControl,
    SID.ReadDataByPeriodicIdentifier + RESPONSE_OFFSET: handleReadDataByPeriodicIdentifier,
    SID.DynamicallyDefineDataIdentifier + RESPONSE_OFFSET: handleDynamicallyDefineDataIdentifier,
    SID.InputOutputControlByIdentifier + RESPONSE_OFFSET: handleInputOutputControlByIdentifier,
    SID.RoutineControl + RESPONSE_OFFSET: handleRoutineControl,
    SID.RequestDownload + RESPONSE_OFFSET: handleRequestDownload,
    SID.RequestUpload + RESPONSE_OFFSET: handleRequestUpload,
    SID.TransferData + RESPONSE_OFFSET: handleTransferData,
    SID.RequestTransferExit + RESPONSE_OFFSET: handleRequestTransferExit,
    SID.TesterPresent + RESPONSE_OFFSET: handleTesterPresent,
    SID.WriteMemoryByAddress + RESPONSE_OFFSET: handleWriteMemoryByAddress,
    SID.AccessTimingParameter + RESPONSE_OFFSET: handleAccessTimingParameter,
    SID.SecuredDataTransmission + RESPONSE_OFFSET: handleSecuredDataTransmission,
    SID.ControlDTCSetting + RESPONSE_OFFSET: handleControlDTCSetting,
    SID.ResponseOnEvent + RESPONSE_OFFSET: handleResponseOnEvent,
    SID.LinkControl + RESPONSE_OFFSET: handleLinkControl,
}