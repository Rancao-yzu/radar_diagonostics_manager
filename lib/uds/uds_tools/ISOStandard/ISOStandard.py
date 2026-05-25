#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


from enum import Enum, IntEnum

RESPONSE_OFFSET = 0x40

class IsoDidNames(Enum):

    bootSoftwareIdentification = "bootSoftwareIdentification"
    applicationSoftwareIdentification = "applicationSoftwareIdentification"

class IsoServices(IntEnum):

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


class IsoDiagnosticSessionType(IntEnum):
    DefaultSession = 0x01
    ProgrammingSession = 0x02
    ExtendedDiagnosticSession = 0x03
    SafetySystemDiagnosticSession = 0x04

class IsoDataIdentifier(IntEnum):
    
    FingerPrint_DID = 0xF15A 
    
    RepairTesterSerNum_DID = 0xF198
    ProgorConfigDate_DID = 0xF199


class IsoRutineControlType(IntEnum):
    startRoutine = 0x01
    stopRoutine = 0x02
    requestRoutineResults = 0x03

class IsoEcuResetType(IntEnum):
    HardReset = 0x01
    KeyOffOnReset = 0x02
    SoftReset = 0x03
    EnableRapidPowerShutDown = 0x04
    DisableRapidPowerShutDown = 0x05

class IsoSecurityAccessType(IntEnum):
    RequestSeed = 0x01
    SendKey = 0x02
    RequestSeedS32K = 0x11
    SendKeyS32K = 0x12

class IsoDTCsubfunction(IntEnum):
    reportNumberOfDTCByStatusMask = 0x01
    reportDTCByStatusMask = 0x02
    reportDTCSnapshotIdentification = 0x03
    reportDTCSnapshotRecordByDTCNumber = 0x04
    reportDTCSnapshotRecordByRecordNumber = 0x05
    reportDTCExtendedDataRecordByDTCNumber = 0x06
    reportNumberOfDTCBySeverityMaskRecord = 0x07
    reportDTCBySeverityMaskRecord = 0x08
    reportSeverityInformationOfDTC = 0x09
    reportSupportedDTC = 0x0A
    reportFirstTestFailedDTC = 0x0B
    reportFirstConfirmedDTC = 0x0C
    reportMostRecentTestFailedDTC = 0x0D
    reportMostRecentConfirmedDTC = 0x0E
    reportMirrorMemoryDTCByStatusMask = 0x0F
    reportMirrorMemoryDTCExtendedDataRecordByDTCNumber = 0x10
    reportNumberOfMirrorMemoryDTCByStatusMask = 0x11
    reportNumberOfEmissionsRelatedOBDDTCByStatusMask = 0x12
    reportEmissionsRelatedOBDDTCByStatusMask = 0x13
    
	
class IsoRoutineControlType(IntEnum):

    startRoutine = 0x01
    stopRoutine = 0x02
    requestRoutineResults = 0x03


class IsoInputOutputControlOptionRecord(IntEnum):

    returnControl = 0x00
    resetToDefault = 0x01
    freezeCurrentState = 0x02
    adjust = 0x03


class IsoReadDTCSubfunction(IntEnum):

    reportNumberOfDTCByStatusMask = 0x01
    reportDTCByStatusMask = 0x02
    reportDTCSnapshotIdentification = 0x03
    reportDTCSnapshotRecordByDTCNumber = 0x04
    reportDTCSnapshotRecordByRecordNumber = 0x05
    reportDTCExtendedDataRecordByDTCNumber = 0x06
    reportNumberOfDTCBySeverityMaskRecord = 0x07
    reportDTCBySeverityMaskRecord = 0x08
    reportSeverityInformationOfDTC = 0x09
    reportSupportedDTC = 0x0A
    reportFirstTestFailedDTC = 0x0B
    reportFirstConfirmedDTC = 0x0C
    reportMostRecentTestFailedDTC = 0x0D
    reportMostRecentConfirmedDTC = 0x0E
    reportMirrorMemoryDTCByStatusMask = 0x0F
    reportMirrorMemoryDTCExtendedDataRecordByDTCNumber = 0x10
    reportNumberOfMirrorMemoryDTCByStatusMask = 0x11
    reportNumberOfEmissionsRelatedOBDDTCByStatusMask = 0x12
    reportEmissionsRelatedOBDDTCByStatusMask = 0x13

	
class IsoReadDTCStatusMask(IntEnum):

    testFailed = 0x01
    testFailedThisMonitoringCycle = 0x02         # ... reserved
    pendingDtc = 0x04                            # ... reserved
    confirmedDtc = 0x08
    testNotCompletedSinceLastClear = 0x10
    testFailedSinceLastClear = 0x20
    testNotCompletedThisMonitoringCycle = 0x40
    warningIndicatorRequested = 0x80             # ... reserved


class IsoDataFormatIdentifier(IntEnum):

    noCompressionMethod = 0x00  # ... for use during request download - all other values are manufacturer specific

	
