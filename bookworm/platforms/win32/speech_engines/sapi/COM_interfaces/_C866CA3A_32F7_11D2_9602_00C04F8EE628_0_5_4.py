# -*- coding: mbcs -*-
typelib_path = "C:\\windows\\System32\\Speech\\Common\\sapi.dll"
_lcid = 0  # change this if required
from ctypes import *
from ctypes import HRESULT

import comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0
from comtypes import BSTR, COMMETHOD, GUID, CoClass, IUnknown, dispid, helpstring

WSTRING = c_wchar_p
from ctypes.wintypes import _LARGE_INTEGER, _ULARGE_INTEGER, VARIANT_BOOL

from comtypes import wireHWND
from comtypes.automation import VARIANT

UINT_PTR = c_ulong
LONG_PTR = c_int
from ctypes.wintypes import _FILETIME

from comtypes import DISPMETHOD, DISPPROPERTY, IServiceProvider, helpstring
from comtypes.automation import VARIANT
from comtypes.typeinfo import ULONG_PTR


class ISpeechPhraseReplacements(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseReplacements Interface"
    _iid_ = GUID("{38BC662F-2257-4525-959E-2069D2596C05}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechPhraseReplacement(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseReplacement Interface"
    _iid_ = GUID("{2890A410-53A7-4FB5-94EC-06D4998E3D02}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechPhraseReplacements._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseReplacement)), "Reps"),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the tokens"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechPhraseReplacements implementation
##class ISpeechPhraseReplacements_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Reps
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the tokens'
##        #return EnumVARIANT
##


class IEnumSpObjectTokens(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "IEnumSpObjectTokens Interface"
    _iid_ = GUID("{06B64F9E-7FDA-11D2-B4F2-00C04F797396}")
    _idlflags_ = ["restricted"]

    def __iter__(self):
        return self

    def next(self):
        item, fetched = self.Next(1)
        if fetched:
            return item
        raise StopIteration

    def __getitem__(self, index):
        self.Reset()
        self.Skip(index)
        item, fetched = self.Next(1)
        if fetched:
            return item
        raise IndexError(index)


class ISpDataKey(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpDataKey Interface"
    _iid_ = GUID("{14056581-E16C-11D2-BB90-00C04F8EE6C0}")
    _idlflags_ = ["restricted"]


class ISpObjectToken(ISpDataKey):
    _case_insensitive_ = True
    "ISpObjectToken Interface"
    _iid_ = GUID("{14056589-E16C-11D2-BB90-00C04F8EE6C0}")
    _idlflags_ = ["restricted"]


IEnumSpObjectTokens._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "Next",
        (["in"], c_ulong, "celt"),
        (["out"], POINTER(POINTER(ISpObjectToken)), "pelt"),
        (["out"], POINTER(c_ulong), "pceltFetched"),
    ),
    COMMETHOD([], HRESULT, "Skip", (["in"], c_ulong, "celt")),
    COMMETHOD([], HRESULT, "Reset"),
    COMMETHOD(
        [], HRESULT, "Clone", (["out"], POINTER(POINTER(IEnumSpObjectTokens)), "ppEnum")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "Item",
        (["in"], c_ulong, "Index"),
        (["out"], POINTER(POINTER(ISpObjectToken)), "ppToken"),
    ),
    COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(c_ulong), "pCount")),
]
################################################################
## code template for IEnumSpObjectTokens implementation
##class IEnumSpObjectTokens_Impl(object):
##    def Next(self, celt):
##        '-no docstring-'
##        #return pelt, pceltFetched
##
##    def Skip(self, celt):
##        '-no docstring-'
##        #return
##
##    def Reset(self):
##        '-no docstring-'
##        #return
##
##    def Clone(self):
##        '-no docstring-'
##        #return ppEnum
##
##    def Item(self, Index):
##        '-no docstring-'
##        #return ppToken
##
##    def GetCount(self):
##        '-no docstring-'
##        #return pCount
##


class ISpeechPhraseProperties(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseProperties Interface"
    _iid_ = GUID("{08166B47-102E-4B23-A599-BDB98DBFD1F4}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechPhraseProperty(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseProperty Interface"
    _iid_ = GUID("{CE563D48-961E-4732-A2E1-378A42B430BE}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechPhraseProperties._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseProperty)), "Property"),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the alternates"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechPhraseProperties implementation
##class ISpeechPhraseProperties_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Property
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the alternates'
##        #return EnumVARIANT
##


class ISpeechPhraseRule(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseRule Interface"
    _iid_ = GUID("{A7BFE112-A4A0-48D9-B602-C313843F6964}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechPhraseRules(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseRules Interface"
    _iid_ = GUID("{9047D593-01DD-4B72-81A3-E4A0CA69F407}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechEngineConfidence'
SECLowConfidence = -1
SECNormalConfidence = 0
SECHighConfidence = 1
SpeechEngineConfidence = c_int  # enum
ISpeechPhraseRule._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Name"), "propget"],
        HRESULT,
        "Name",
        (["out", "retval"], POINTER(BSTR), "Name"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Id"), "propget"],
        HRESULT,
        "Id",
        (["out", "retval"], POINTER(c_int), "Id"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("FirstElement"), "propget"],
        HRESULT,
        "FirstElement",
        (["out", "retval"], POINTER(c_int), "FirstElement"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("NumElements"), "propget"],
        HRESULT,
        "NumberOfElements",
        (["out", "retval"], POINTER(c_int), "NumberOfElements"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("Parent"), "propget"],
        HRESULT,
        "Parent",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseRule)), "Parent"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("Children"), "propget"],
        HRESULT,
        "Children",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseRules)), "Children"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("Confidence"), "propget"],
        HRESULT,
        "Confidence",
        (["out", "retval"], POINTER(SpeechEngineConfidence), "ActualConfidence"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("EngineConfidence"), "propget"],
        HRESULT,
        "EngineConfidence",
        (["out", "retval"], POINTER(c_float), "EngineConfidence"),
    ),
]
################################################################
## code template for ISpeechPhraseRule implementation
##class ISpeechPhraseRule_Impl(object):
##    @property
##    def Name(self):
##        'Name'
##        #return Name
##
##    @property
##    def Id(self):
##        'Id'
##        #return Id
##
##    @property
##    def FirstElement(self):
##        'FirstElement'
##        #return FirstElement
##
##    @property
##    def NumberOfElements(self):
##        'NumElements'
##        #return NumberOfElements
##
##    @property
##    def Parent(self):
##        'Parent'
##        #return Parent
##
##    @property
##    def Children(self):
##        'Children'
##        #return Children
##
##    @property
##    def Confidence(self):
##        'Confidence'
##        #return ActualConfidence
##
##    @property
##    def EngineConfidence(self):
##        'EngineConfidence'
##        #return EngineConfidence
##

ISpeechPhraseRules._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseRule)), "Rule"),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the Rules"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechPhraseRules implementation
##class ISpeechPhraseRules_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Rule
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the Rules'
##        #return EnumVARIANT
##


class SpResourceManager(CoClass):
    "SpResourceManger"
    _reg_clsid_ = GUID("{96749373-3391-11D2-9EE3-00C04F797396}")
    _idlflags_ = ["hidden", "restricted"]
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpResourceManager(IServiceProvider):
    _case_insensitive_ = True
    "ISpResourceManager Interface"
    _iid_ = GUID("{93384E18-5014-43D5-ADBB-A78E055926BD}")
    _idlflags_ = ["restricted"]


SpResourceManager._com_interfaces_ = [ISpResourceManager]


# values for enumeration 'SPDATAKEYLOCATION'
SPDKL_DefaultLocation = 0
SPDKL_CurrentUser = 1
SPDKL_LocalMachine = 2
SPDKL_CurrentConfig = 5
SPDATAKEYLOCATION = c_int  # enum
ISpDataKey._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetData",
        (["in"], WSTRING, "pszValueName"),
        (["in"], c_ulong, "cbData"),
        (["in"], POINTER(c_ubyte), "pData"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetData",
        (["in"], WSTRING, "pszValueName"),
        (["in"], POINTER(c_ulong), "pcbData"),
        (["out"], POINTER(c_ubyte), "pData"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetStringValue",
        (["in"], WSTRING, "pszValueName"),
        (["in"], WSTRING, "pszValue"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetStringValue",
        (["in"], WSTRING, "pszValueName"),
        (["out"], POINTER(WSTRING), "ppszValue"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetDWORD",
        (["in"], WSTRING, "pszValueName"),
        (["in"], c_ulong, "dwValue"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetDWORD",
        (["in"], WSTRING, "pszValueName"),
        (["out"], POINTER(c_ulong), "pdwValue"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "OpenKey",
        (["in"], WSTRING, "pszSubKeyName"),
        (["out"], POINTER(POINTER(ISpDataKey)), "ppSubKey"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "CreateKey",
        (["in"], WSTRING, "pszSubKey"),
        (["out"], POINTER(POINTER(ISpDataKey)), "ppSubKey"),
    ),
    COMMETHOD([], HRESULT, "DeleteKey", (["in"], WSTRING, "pszSubKey")),
    COMMETHOD([], HRESULT, "DeleteValue", (["in"], WSTRING, "pszValueName")),
    COMMETHOD(
        [],
        HRESULT,
        "EnumKeys",
        (["in"], c_ulong, "Index"),
        (["out"], POINTER(WSTRING), "ppszSubKeyName"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "EnumValues",
        (["in"], c_ulong, "Index"),
        (["out"], POINTER(WSTRING), "ppszValueName"),
    ),
]
################################################################
## code template for ISpDataKey implementation
##class ISpDataKey_Impl(object):
##    def SetData(self, pszValueName, cbData, pData):
##        '-no docstring-'
##        #return
##
##    def GetData(self, pszValueName, pcbData):
##        '-no docstring-'
##        #return pData
##
##    def SetStringValue(self, pszValueName, pszValue):
##        '-no docstring-'
##        #return
##
##    def GetStringValue(self, pszValueName):
##        '-no docstring-'
##        #return ppszValue
##
##    def SetDWORD(self, pszValueName, dwValue):
##        '-no docstring-'
##        #return
##
##    def GetDWORD(self, pszValueName):
##        '-no docstring-'
##        #return pdwValue
##
##    def OpenKey(self, pszSubKeyName):
##        '-no docstring-'
##        #return ppSubKey
##
##    def CreateKey(self, pszSubKey):
##        '-no docstring-'
##        #return ppSubKey
##
##    def DeleteKey(self, pszSubKey):
##        '-no docstring-'
##        #return
##
##    def DeleteValue(self, pszValueName):
##        '-no docstring-'
##        #return
##
##    def EnumKeys(self, Index):
##        '-no docstring-'
##        #return ppszSubKeyName
##
##    def EnumValues(self, Index):
##        '-no docstring-'
##        #return ppszValueName
##


class ISpObjectTokenCategory(ISpDataKey):
    _case_insensitive_ = True
    "ISpObjectTokenCategory"
    _iid_ = GUID("{2D3D3845-39AF-4850-BBF9-40B49780011D}")
    _idlflags_ = ["restricted"]


ISpObjectToken._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetId",
        ([], WSTRING, "pszCategoryId"),
        (["in"], WSTRING, "pszTokenId"),
        (["in"], c_int, "fCreateIfNotExist"),
    ),
    COMMETHOD([], HRESULT, "GetId", (["out"], POINTER(WSTRING), "ppszCoMemTokenId")),
    COMMETHOD(
        [],
        HRESULT,
        "GetCategory",
        (["out"], POINTER(POINTER(ISpObjectTokenCategory)), "ppTokenCategory"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "CreateInstance",
        (["in"], POINTER(IUnknown), "pUnkOuter"),
        (["in"], c_ulong, "dwClsContext"),
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "riid",
        ),
        (["out"], POINTER(c_void_p), "ppvObject"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetStorageFileName",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "clsidCaller",
        ),
        (["in"], WSTRING, "pszValueName"),
        (["in"], WSTRING, "pszFileNameSpecifier"),
        (["in"], c_ulong, "nFolder"),
        (["out"], POINTER(WSTRING), "ppszFilePath"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "RemoveStorageFileName",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "clsidCaller",
        ),
        (["in"], WSTRING, "pszKeyName"),
        (["in"], c_int, "fDeleteFile"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "Remove",
        (
            [],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pclsidCaller",
        ),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "IsUISupported",
        (["in"], WSTRING, "pszTypeOfUI"),
        (["in"], c_void_p, "pvExtraData"),
        (["in"], c_ulong, "cbExtraData"),
        (["in"], POINTER(IUnknown), "punkObject"),
        (["out"], POINTER(c_int), "pfSupported"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "DisplayUI",
        (["in"], wireHWND, "hWndParent"),
        (["in"], WSTRING, "pszTitle"),
        (["in"], WSTRING, "pszTypeOfUI"),
        (["in"], c_void_p, "pvExtraData"),
        (["in"], c_ulong, "cbExtraData"),
        (["in"], POINTER(IUnknown), "punkObject"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "MatchesAttributes",
        (["in"], WSTRING, "pszAttributes"),
        (["out"], POINTER(c_int), "pfMatches"),
    ),
]
################################################################
## code template for ISpObjectToken implementation
##class ISpObjectToken_Impl(object):
##    def SetId(self, pszCategoryId, pszTokenId, fCreateIfNotExist):
##        '-no docstring-'
##        #return
##
##    def GetId(self):
##        '-no docstring-'
##        #return ppszCoMemTokenId
##
##    def GetCategory(self):
##        '-no docstring-'
##        #return ppTokenCategory
##
##    def CreateInstance(self, pUnkOuter, dwClsContext, riid):
##        '-no docstring-'
##        #return ppvObject
##
##    def GetStorageFileName(self, clsidCaller, pszValueName, pszFileNameSpecifier, nFolder):
##        '-no docstring-'
##        #return ppszFilePath
##
##    def RemoveStorageFileName(self, clsidCaller, pszKeyName, fDeleteFile):
##        '-no docstring-'
##        #return
##
##    def Remove(self, pclsidCaller):
##        '-no docstring-'
##        #return
##
##    def IsUISupported(self, pszTypeOfUI, pvExtraData, cbExtraData, punkObject):
##        '-no docstring-'
##        #return pfSupported
##
##    def DisplayUI(self, hWndParent, pszTitle, pszTypeOfUI, pvExtraData, cbExtraData, punkObject):
##        '-no docstring-'
##        #return
##
##    def MatchesAttributes(self, pszAttributes):
##        '-no docstring-'
##        #return pfMatches
##

ISpeechPhraseProperty._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Name"), "propget"],
        HRESULT,
        "Name",
        (["out", "retval"], POINTER(BSTR), "Name"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Id"), "propget"],
        HRESULT,
        "Id",
        (["out", "retval"], POINTER(c_int), "Id"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Value"), "propget"],
        HRESULT,
        "Value",
        (["out", "retval"], POINTER(VARIANT), "Value"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("FirstElement"), "propget"],
        HRESULT,
        "FirstElement",
        (["out", "retval"], POINTER(c_int), "FirstElement"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("NumberOfElements"), "propget"],
        HRESULT,
        "NumberOfElements",
        (["out", "retval"], POINTER(c_int), "NumberOfElements"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("EngineConfidence"), "propget"],
        HRESULT,
        "EngineConfidence",
        (["out", "retval"], POINTER(c_float), "Confidence"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("Confidence"), "propget"],
        HRESULT,
        "Confidence",
        (["out", "retval"], POINTER(SpeechEngineConfidence), "Confidence"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("Parent"), "propget"],
        HRESULT,
        "Parent",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseProperty)), "ParentProperty"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("Children"), "propget"],
        HRESULT,
        "Children",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseProperties)), "Children"),
    ),
]
################################################################
## code template for ISpeechPhraseProperty implementation
##class ISpeechPhraseProperty_Impl(object):
##    @property
##    def Name(self):
##        'Name'
##        #return Name
##
##    @property
##    def Id(self):
##        'Id'
##        #return Id
##
##    @property
##    def Value(self):
##        'Value'
##        #return Value
##
##    @property
##    def FirstElement(self):
##        'FirstElement'
##        #return FirstElement
##
##    @property
##    def NumberOfElements(self):
##        'NumberOfElements'
##        #return NumberOfElements
##
##    @property
##    def EngineConfidence(self):
##        'EngineConfidence'
##        #return Confidence
##
##    @property
##    def Confidence(self):
##        'Confidence'
##        #return Confidence
##
##    @property
##    def Parent(self):
##        'Parent'
##        #return ParentProperty
##
##    @property
##    def Children(self):
##        'Children'
##        #return Children
##


class ISpeechPhraseElements(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseElements Interface"
    _iid_ = GUID("{0626B328-3478-467D-A0B3-D0853B93DDA3}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechPhraseElement(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseElement Interface"
    _iid_ = GUID("{E6176F96-E373-4801-B223-3B62C068C0B4}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechPhraseElements._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseElement)), "Element"),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the tokens"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechPhraseElements implementation
##class ISpeechPhraseElements_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Element
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the tokens'
##        #return EnumVARIANT
##


class SpObjectToken(CoClass):
    "SpObjectToken Class"
    _reg_clsid_ = GUID("{EF411752-3736-4CB4-9C8C-8EF4CCB58EFE}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpeechObjectToken(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechObjectToken Interface"
    _iid_ = GUID("{C74A3ADC-B727-4500-A84A-B526721C8B8C}")
    _idlflags_ = ["dual", "oleautomation"]


SpObjectToken._com_interfaces_ = [ISpeechObjectToken, ISpObjectToken]


class ISequentialStream(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    _iid_ = GUID("{0C733A30-2A1C-11CE-ADE5-00AA0044773D}")
    _idlflags_ = []


class IStream(ISequentialStream):
    _case_insensitive_ = True
    _iid_ = GUID("{0000000C-0000-0000-C000-000000000046}")
    _idlflags_ = []


class ISpStreamFormat(IStream):
    _case_insensitive_ = True
    "ISpStreamFormat Interface"
    _iid_ = GUID("{BED530BE-2606-4F4D-A1C0-54C5CDA5566F}")
    _idlflags_ = ["restricted"]


class ISpAudio(ISpStreamFormat):
    _case_insensitive_ = True
    "ISpAudio Interface"
    _iid_ = GUID("{C05C768F-FAE8-4EC2-8E07-338321C12452}")
    _idlflags_ = ["restricted"]


ISequentialStream._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "RemoteRead",
        (["out"], POINTER(c_ubyte), "pv"),
        (["in"], c_ulong, "cb"),
        (["out"], POINTER(c_ulong), "pcbRead"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "RemoteWrite",
        (["in"], POINTER(c_ubyte), "pv"),
        (["in"], c_ulong, "cb"),
        (["out"], POINTER(c_ulong), "pcbWritten"),
    ),
]
################################################################
## code template for ISequentialStream implementation
##class ISequentialStream_Impl(object):
##    def RemoteRead(self, cb):
##        '-no docstring-'
##        #return pv, pcbRead
##
##    def RemoteWrite(self, pv, cb):
##        '-no docstring-'
##        #return pcbWritten
##


class tagSTATSTG(Structure):
    pass


IStream._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "RemoteSeek",
        (["in"], _LARGE_INTEGER, "dlibMove"),
        (["in"], c_ulong, "dwOrigin"),
        (["out"], POINTER(_ULARGE_INTEGER), "plibNewPosition"),
    ),
    COMMETHOD([], HRESULT, "SetSize", (["in"], _ULARGE_INTEGER, "libNewSize")),
    COMMETHOD(
        [],
        HRESULT,
        "RemoteCopyTo",
        (["in"], POINTER(IStream), "pstm"),
        (["in"], _ULARGE_INTEGER, "cb"),
        (["out"], POINTER(_ULARGE_INTEGER), "pcbRead"),
        (["out"], POINTER(_ULARGE_INTEGER), "pcbWritten"),
    ),
    COMMETHOD([], HRESULT, "Commit", (["in"], c_ulong, "grfCommitFlags")),
    COMMETHOD([], HRESULT, "Revert"),
    COMMETHOD(
        [],
        HRESULT,
        "LockRegion",
        (["in"], _ULARGE_INTEGER, "libOffset"),
        (["in"], _ULARGE_INTEGER, "cb"),
        (["in"], c_ulong, "dwLockType"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "UnlockRegion",
        (["in"], _ULARGE_INTEGER, "libOffset"),
        (["in"], _ULARGE_INTEGER, "cb"),
        (["in"], c_ulong, "dwLockType"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "Stat",
        (["out"], POINTER(tagSTATSTG), "pstatstg"),
        (["in"], c_ulong, "grfStatFlag"),
    ),
    COMMETHOD([], HRESULT, "Clone", (["out"], POINTER(POINTER(IStream)), "ppstm")),
]
################################################################
## code template for IStream implementation
##class IStream_Impl(object):
##    def RemoteSeek(self, dlibMove, dwOrigin):
##        '-no docstring-'
##        #return plibNewPosition
##
##    def SetSize(self, libNewSize):
##        '-no docstring-'
##        #return
##
##    def RemoteCopyTo(self, pstm, cb):
##        '-no docstring-'
##        #return pcbRead, pcbWritten
##
##    def Commit(self, grfCommitFlags):
##        '-no docstring-'
##        #return
##
##    def Revert(self):
##        '-no docstring-'
##        #return
##
##    def LockRegion(self, libOffset, cb, dwLockType):
##        '-no docstring-'
##        #return
##
##    def UnlockRegion(self, libOffset, cb, dwLockType):
##        '-no docstring-'
##        #return
##
##    def Stat(self, grfStatFlag):
##        '-no docstring-'
##        #return pstatstg
##
##    def Clone(self):
##        '-no docstring-'
##        #return ppstm
##


class WAVEFORMATEX(Structure):
    pass


ISpStreamFormat._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetFormat",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pguidFormatId",
        ),
        (["out"], POINTER(POINTER(WAVEFORMATEX)), "ppCoMemWaveFormatEx"),
    ),
]
################################################################
## code template for ISpStreamFormat implementation
##class ISpStreamFormat_Impl(object):
##    def GetFormat(self, pguidFormatId):
##        '-no docstring-'
##        #return ppCoMemWaveFormatEx
##


# values for enumeration '_SPAUDIOSTATE'
SPAS_CLOSED = 0
SPAS_STOP = 1
SPAS_PAUSE = 2
SPAS_RUN = 3
_SPAUDIOSTATE = c_int  # enum
SPAUDIOSTATE = _SPAUDIOSTATE


class SPAUDIOSTATUS(Structure):
    pass


class SPAUDIOBUFFERINFO(Structure):
    pass


ISpAudio._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetState",
        (["in"], SPAUDIOSTATE, "NewState"),
        (["in"], c_ulonglong, "ullReserved"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetFormat",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "rguidFmtId",
        ),
        (["in"], POINTER(WAVEFORMATEX), "pWaveFormatEx"),
    ),
    COMMETHOD([], HRESULT, "GetStatus", (["out"], POINTER(SPAUDIOSTATUS), "pStatus")),
    COMMETHOD(
        [], HRESULT, "SetBufferInfo", (["in"], POINTER(SPAUDIOBUFFERINFO), "pBuffInfo")
    ),
    COMMETHOD(
        [], HRESULT, "GetBufferInfo", (["out"], POINTER(SPAUDIOBUFFERINFO), "pBuffInfo")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetDefaultFormat",
        (
            ["out"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pFormatId",
        ),
        (["out"], POINTER(POINTER(WAVEFORMATEX)), "ppCoMemWaveFormatEx"),
    ),
    COMMETHOD([], c_void_p, "EventHandle"),
    COMMETHOD([], HRESULT, "GetVolumeLevel", (["out"], POINTER(c_ulong), "pLevel")),
    COMMETHOD([], HRESULT, "SetVolumeLevel", (["in"], c_ulong, "Level")),
    COMMETHOD(
        [], HRESULT, "GetBufferNotifySize", (["out"], POINTER(c_ulong), "pcbSize")
    ),
    COMMETHOD([], HRESULT, "SetBufferNotifySize", (["in"], c_ulong, "cbSize")),
]
################################################################
## code template for ISpAudio implementation
##class ISpAudio_Impl(object):
##    def SetState(self, NewState, ullReserved):
##        '-no docstring-'
##        #return
##
##    def SetFormat(self, rguidFmtId, pWaveFormatEx):
##        '-no docstring-'
##        #return
##
##    def GetStatus(self):
##        '-no docstring-'
##        #return pStatus
##
##    def SetBufferInfo(self, pBuffInfo):
##        '-no docstring-'
##        #return
##
##    def GetBufferInfo(self):
##        '-no docstring-'
##        #return pBuffInfo
##
##    def GetDefaultFormat(self):
##        '-no docstring-'
##        #return pFormatId, ppCoMemWaveFormatEx
##
##    def EventHandle(self):
##        '-no docstring-'
##        #return
##
##    def GetVolumeLevel(self):
##        '-no docstring-'
##        #return pLevel
##
##    def SetVolumeLevel(self, Level):
##        '-no docstring-'
##        #return
##
##    def GetBufferNotifySize(self):
##        '-no docstring-'
##        #return pcbSize
##
##    def SetBufferNotifySize(self, cbSize):
##        '-no docstring-'
##        #return
##


# values for enumeration 'DISPID_SpeechVoice'
DISPID_SVStatus = 1
DISPID_SVVoice = 2
DISPID_SVAudioOutput = 3
DISPID_SVAudioOutputStream = 4
DISPID_SVRate = 5
DISPID_SVVolume = 6
DISPID_SVAllowAudioOuputFormatChangesOnNextSet = 7
DISPID_SVEventInterests = 8
DISPID_SVPriority = 9
DISPID_SVAlertBoundary = 10
DISPID_SVSyncronousSpeakTimeout = 11
DISPID_SVSpeak = 12
DISPID_SVSpeakStream = 13
DISPID_SVPause = 14
DISPID_SVResume = 15
DISPID_SVSkip = 16
DISPID_SVGetVoices = 17
DISPID_SVGetAudioOutputs = 18
DISPID_SVWaitUntilDone = 19
DISPID_SVSpeakCompleteEvent = 20
DISPID_SVIsUISupported = 21
DISPID_SVDisplayUI = 22
DISPID_SpeechVoice = c_int  # enum

# values for enumeration 'DISPID_SpeechMMSysAudio'
DISPID_SMSADeviceId = 300
DISPID_SMSALineId = 301
DISPID_SMSAMMHandle = 302
DISPID_SpeechMMSysAudio = c_int  # enum

# values for enumeration 'DISPID_SpeechRecognizerStatus'
DISPID_SRSAudioStatus = 1
DISPID_SRSCurrentStreamPosition = 2
DISPID_SRSCurrentStreamNumber = 3
DISPID_SRSNumberOfActiveRules = 4
DISPID_SRSClsidEngine = 5
DISPID_SRSSupportedLanguages = 6
DISPID_SpeechRecognizerStatus = c_int  # enum
SpeechGrammarTagWildcard = "..."  # Constant BSTR

# values for enumeration 'DISPID_SpeechVoiceStatus'
DISPID_SVSCurrentStreamNumber = 1
DISPID_SVSLastStreamNumberQueued = 2
DISPID_SVSLastResult = 3
DISPID_SVSRunningState = 4
DISPID_SVSInputWordPosition = 5
DISPID_SVSInputWordLength = 6
DISPID_SVSInputSentencePosition = 7
DISPID_SVSInputSentenceLength = 8
DISPID_SVSLastBookmark = 9
DISPID_SVSLastBookmarkId = 10
DISPID_SVSPhonemeId = 11
DISPID_SVSVisemeId = 12
DISPID_SpeechVoiceStatus = c_int  # enum

# values for enumeration 'DISPID_SpeechBaseStream'
DISPID_SBSFormat = 1
DISPID_SBSRead = 2
DISPID_SBSWrite = 3
DISPID_SBSSeek = 4
DISPID_SpeechBaseStream = c_int  # enum
SpeechTokenValueCLSID = "CLSID"  # Constant BSTR


class ISpeechTextSelectionInformation(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechTextSelectionInformation Interface"
    _iid_ = GUID("{3B9C7E7A-6EEE-4DED-9092-11657279ADBE}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechTextSelectionInformation._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("ActiveOffset"), "propput"],
        HRESULT,
        "ActiveOffset",
        (["in"], c_int, "ActiveOffset"),
    ),
    COMMETHOD(
        [dispid(1), helpstring("ActiveOffset"), "propget"],
        HRESULT,
        "ActiveOffset",
        (["out", "retval"], POINTER(c_int), "ActiveOffset"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("ActiveLength"), "propput"],
        HRESULT,
        "ActiveLength",
        (["in"], c_int, "ActiveLength"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("ActiveLength"), "propget"],
        HRESULT,
        "ActiveLength",
        (["out", "retval"], POINTER(c_int), "ActiveLength"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("SelectionOffset"), "propput"],
        HRESULT,
        "SelectionOffset",
        (["in"], c_int, "SelectionOffset"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("SelectionOffset"), "propget"],
        HRESULT,
        "SelectionOffset",
        (["out", "retval"], POINTER(c_int), "SelectionOffset"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("SelectionLength"), "propput"],
        HRESULT,
        "SelectionLength",
        (["in"], c_int, "SelectionLength"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("SelectionLength"), "propget"],
        HRESULT,
        "SelectionLength",
        (["out", "retval"], POINTER(c_int), "SelectionLength"),
    ),
]
################################################################
## code template for ISpeechTextSelectionInformation implementation
##class ISpeechTextSelectionInformation_Impl(object):
##    def _get(self):
##        'ActiveOffset'
##        #return ActiveOffset
##    def _set(self, ActiveOffset):
##        'ActiveOffset'
##    ActiveOffset = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'ActiveLength'
##        #return ActiveLength
##    def _set(self, ActiveLength):
##        'ActiveLength'
##    ActiveLength = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'SelectionOffset'
##        #return SelectionOffset
##    def _set(self, SelectionOffset):
##        'SelectionOffset'
##    SelectionOffset = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'SelectionLength'
##        #return SelectionLength
##    def _set(self, SelectionLength):
##        'SelectionLength'
##    SelectionLength = property(_get, _set, doc = _set.__doc__)
##

SpeechCategoryRecognizers = (
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Recognizers"  # Constant BSTR
)
SpeechCategoryAppLexicons = (
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\AppLexicons"  # Constant BSTR
)
SpeechCategoryPhoneConverters = (
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\PhoneConverters"  # Constant BSTR
)
SpeechCategoryRecoProfiles = (
    "HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Speech\\RecoProfiles"  # Constant BSTR
)
SpeechTokenIdUserLexicon = "HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Speech\\CurrentUserLexicon"  # Constant BSTR
SpeechTokenKeyFiles = "Files"  # Constant BSTR

# values for enumeration 'SpeechLoadOption'
SLOStatic = 0
SLODynamic = 1
SpeechLoadOption = c_int  # enum
SpeechTokenKeyUI = "UI"  # Constant BSTR
SpeechGrammarTagUnlimitedDictation = "*+"  # Constant BSTR
SpeechTokenKeyAttributes = "Attributes"  # Constant BSTR
SpeechVoiceCategoryTTSRate = "DefaultTTSRate"  # Constant BSTR

# values for enumeration 'DISPID_SpeechRecognizer'
DISPID_SRRecognizer = 1
DISPID_SRAllowAudioInputFormatChangesOnNextSet = 2
DISPID_SRAudioInput = 3
DISPID_SRAudioInputStream = 4
DISPID_SRIsShared = 5
DISPID_SRState = 6
DISPID_SRStatus = 7
DISPID_SRProfile = 8
DISPID_SREmulateRecognition = 9
DISPID_SRCreateRecoContext = 10
DISPID_SRGetFormat = 11
DISPID_SRSetPropertyNumber = 12
DISPID_SRGetPropertyNumber = 13
DISPID_SRSetPropertyString = 14
DISPID_SRGetPropertyString = 15
DISPID_SRIsUISupported = 16
DISPID_SRDisplayUI = 17
DISPID_SRGetRecognizers = 18
DISPID_SVGetAudioInputs = 19
DISPID_SVGetProfiles = 20
DISPID_SpeechRecognizer = c_int  # enum
SpeechPropertyResourceUsage = "ResourceUsage"  # Constant BSTR
SpeechPropertyHighConfidenceThreshold = "HighConfidenceThreshold"  # Constant BSTR
SpeechPropertyNormalConfidenceThreshold = "NormalConfidenceThreshold"  # Constant BSTR
SpeechPropertyLowConfidenceThreshold = "LowConfidenceThreshold"  # Constant BSTR
SpeechPropertyResponseSpeed = "ResponseSpeed"  # Constant BSTR
SpeechPropertyComplexResponseSpeed = "ComplexResponseSpeed"  # Constant BSTR
SpeechPropertyAdaptationOn = "AdaptationOn"  # Constant BSTR
SpeechDictationTopicSpelling = "Spelling"  # Constant BSTR

# values for enumeration 'SpeechRuleState'
SGDSInactive = 0
SGDSActive = 1
SGDSActiveWithAutoPause = 3
SGDSActiveUserDelimited = 4
SpeechRuleState = c_int  # enum

# values for enumeration 'DISPID_SpeechAudio'
DISPID_SAStatus = 200
DISPID_SABufferInfo = 201
DISPID_SADefaultFormat = 202
DISPID_SAVolume = 203
DISPID_SABufferNotifySize = 204
DISPID_SAEventHandle = 205
DISPID_SASetState = 206
DISPID_SpeechAudio = c_int  # enum
SpeechGrammarTagDictation = "*"  # Constant BSTR
SPAUDIOSTATUS._fields_ = [
    ("cbFreeBuffSpace", c_int),
    ("cbNonBlockingIO", c_ulong),
    ("State", SPAUDIOSTATE),
    ("CurSeekPos", c_ulonglong),
    ("CurDevicePos", c_ulonglong),
    ("dwAudioLevel", c_ulong),
    ("dwReserved2", c_ulong),
]
assert sizeof(SPAUDIOSTATUS) == 40, sizeof(SPAUDIOSTATUS)
assert alignment(SPAUDIOSTATUS) == 8, alignment(SPAUDIOSTATUS)

# values for enumeration 'DISPID_SpeechObjectTokens'
DISPID_SOTsCount = 1
DISPID_SOTsItem = 0
DISPID_SOTs_NewEnum = -4
DISPID_SpeechObjectTokens = c_int  # enum
SPAUDIOBUFFERINFO._fields_ = [
    ("ulMsMinNotification", c_ulong),
    ("ulMsBufferSize", c_ulong),
    ("ulMsEventBias", c_ulong),
]
assert sizeof(SPAUDIOBUFFERINFO) == 12, sizeof(SPAUDIOBUFFERINFO)
assert alignment(SPAUDIOBUFFERINFO) == 4, alignment(SPAUDIOBUFFERINFO)
SpeechEngineProperties = "EngineProperties"  # Constant BSTR


class SPVOICESTATUS(Structure):
    pass


# values for enumeration 'SPVISEMES'
SP_VISEME_0 = 0
SP_VISEME_1 = 1
SP_VISEME_2 = 2
SP_VISEME_3 = 3
SP_VISEME_4 = 4
SP_VISEME_5 = 5
SP_VISEME_6 = 6
SP_VISEME_7 = 7
SP_VISEME_8 = 8
SP_VISEME_9 = 9
SP_VISEME_10 = 10
SP_VISEME_11 = 11
SP_VISEME_12 = 12
SP_VISEME_13 = 13
SP_VISEME_14 = 14
SP_VISEME_15 = 15
SP_VISEME_16 = 16
SP_VISEME_17 = 17
SP_VISEME_18 = 18
SP_VISEME_19 = 19
SP_VISEME_20 = 20
SP_VISEME_21 = 21
SPVISEMES = c_int  # enum
SPVOICESTATUS._fields_ = [
    ("ulCurrentStream", c_ulong),
    ("ulLastStreamQueued", c_ulong),
    ("hrLastResult", HRESULT),
    ("dwRunningState", c_ulong),
    ("ulInputWordPos", c_ulong),
    ("ulInputWordLen", c_ulong),
    ("ulInputSentPos", c_ulong),
    ("ulInputSentLen", c_ulong),
    ("lBookmarkId", c_int),
    ("PhonemeId", c_ushort),
    ("VisemeId", SPVISEMES),
    ("dwReserved1", c_ulong),
    ("dwReserved2", c_ulong),
]
assert sizeof(SPVOICESTATUS) == 52, sizeof(SPVOICESTATUS)
assert alignment(SPVOICESTATUS) == 4, alignment(SPVOICESTATUS)
SpeechAddRemoveWord = "AddRemoveWord"  # Constant BSTR
SpeechUserTraining = "UserTraining"  # Constant BSTR
SpeechMicTraining = "MicTraining"  # Constant BSTR

# values for enumeration 'DISPID_SpeechVoiceEvent'
DISPID_SVEStreamStart = 1
DISPID_SVEStreamEnd = 2
DISPID_SVEVoiceChange = 3
DISPID_SVEBookmark = 4
DISPID_SVEWord = 5
DISPID_SVEPhoneme = 6
DISPID_SVESentenceBoundary = 7
DISPID_SVEViseme = 8
DISPID_SVEAudioLevel = 9
DISPID_SVEEnginePrivate = 10
DISPID_SpeechVoiceEvent = c_int  # enum
SpeechRecoProfileProperties = "RecoProfileProperties"  # Constant BSTR
SpeechAudioProperties = "AudioProperties"  # Constant BSTR
SpeechAudioVolume = "AudioVolume"  # Constant BSTR
SpeechVoiceSkipTypeSentence = "Sentence"  # Constant BSTR
SpeechAudioFormatGUIDWave = "{C31ADBAE-527F-4ff5-A230-F62BB61FF70C}"  # Constant BSTR
SpeechAudioFormatGUIDText = "{7CEEF9F9-3D13-11d2-9EE7-00C04F797396}"  # Constant BSTR
Speech_Default_Weight = 1.0  # Constant c_float
Speech_Max_Word_Length = 128  # Constant c_int
Speech_Max_Pron_Length = 384  # Constant c_int
Speech_StreamPos_Asap = 0  # Constant c_int
Speech_StreamPos_RealTime = -1  # Constant c_int
SpeechAllElements = -1  # Constant c_int

# values for enumeration 'DISPID_SpeechDataKey'
DISPID_SDKSetBinaryValue = 1
DISPID_SDKGetBinaryValue = 2
DISPID_SDKSetStringValue = 3
DISPID_SDKGetStringValue = 4
DISPID_SDKSetLongValue = 5
DISPID_SDKGetlongValue = 6
DISPID_SDKOpenKey = 7
DISPID_SDKCreateKey = 8
DISPID_SDKDeleteKey = 9
DISPID_SDKDeleteValue = 10
DISPID_SDKEnumKeys = 11
DISPID_SDKEnumValues = 12
DISPID_SpeechDataKey = c_int  # enum

# values for enumeration 'DISPID_SpeechObjectToken'
DISPID_SOTId = 1
DISPID_SOTDataKey = 2
DISPID_SOTCategory = 3
DISPID_SOTGetDescription = 4
DISPID_SOTSetId = 5
DISPID_SOTGetAttribute = 6
DISPID_SOTCreateInstance = 7
DISPID_SOTRemove = 8
DISPID_SOTGetStorageFileName = 9
DISPID_SOTRemoveStorageFileName = 10
DISPID_SOTIsUISupported = 11
DISPID_SOTDisplayUI = 12
DISPID_SOTMatchesAttributes = 13
DISPID_SpeechObjectToken = c_int  # enum

# values for enumeration 'SpeechEmulationCompareFlags'
SECFIgnoreCase = 1
SECFIgnoreKanaType = 65536
SECFIgnoreWidth = 131072
SECFNoSpecialChars = 536870912
SECFEmulateResult = 1073741824
SECFDefault = 196609
SpeechEmulationCompareFlags = c_int  # enum


class ISpeechRecoResult(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechRecoResult Interface"
    _iid_ = GUID("{ED2879CF-CED9-4EE6-A534-DE0191D5468D}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechRecoContext(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechRecoContext Interface"
    _iid_ = GUID("{580AA49D-7E1E-4809-B8E2-57DA806104B8}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechRecoResultTimes(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechRecoResultTimes Interface"
    _iid_ = GUID("{62B3B8FB-F6E7-41BE-BDCB-056B1C29EFC0}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechAudioFormat(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechAudioFormat Interface"
    _iid_ = GUID("{E6E9C590-3E18-40E3-8299-061F98BDE7C7}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechPhraseInfo(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseInfo Interface"
    _iid_ = GUID("{961559CF-4E67-4662-8BF0-D93F1FCD61B3}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechPhraseAlternates(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseAlternates Interface"
    _iid_ = GUID("{B238B6D5-F276-4C3D-A6C1-2974801C3CC2}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechBaseStream(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechBaseStream Interface"
    _iid_ = GUID("{6450336F-7D49-4CED-8097-49D6DEE37294}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechMemoryStream(ISpeechBaseStream):
    _case_insensitive_ = True
    "ISpeechMemoryStream Interface"
    _iid_ = GUID("{EEB14B68-808B-4ABE-A5EA-B51DA7588008}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechVoiceSpeakFlags'
SVSFDefault = 0
SVSFlagsAsync = 1
SVSFPurgeBeforeSpeak = 2
SVSFIsFilename = 4
SVSFIsXML = 8
SVSFIsNotXML = 16
SVSFPersistXML = 32
SVSFNLPSpeakPunc = 64
SVSFParseSapi = 128
SVSFParseSsml = 256
SVSFParseAutodetect = 0
SVSFNLPMask = 64
SVSFParseMask = 384
SVSFVoiceMask = 511
SVSFUnusedFlags = -512
SpeechVoiceSpeakFlags = c_int  # enum

# values for enumeration 'SpeechDiscardType'
SDTProperty = 1
SDTReplacement = 2
SDTRule = 4
SDTDisplayText = 8
SDTLexicalForm = 16
SDTPronunciation = 32
SDTAudio = 64
SDTAlternates = 128
SDTAll = 255
SpeechDiscardType = c_int  # enum
ISpeechRecoResult._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("RecoContext"), "propget"],
        HRESULT,
        "RecoContext",
        (["out", "retval"], POINTER(POINTER(ISpeechRecoContext)), "RecoContext"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Times"), "propget"],
        HRESULT,
        "Times",
        (["out", "retval"], POINTER(POINTER(ISpeechRecoResultTimes)), "Times"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AudioFormat"), "propputref"],
        HRESULT,
        "AudioFormat",
        (["in"], POINTER(ISpeechAudioFormat), "Format"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AudioFormat"), "propget"],
        HRESULT,
        "AudioFormat",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioFormat)), "Format"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("PhraseInfo"), "propget"],
        HRESULT,
        "PhraseInfo",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseInfo)), "PhraseInfo"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("Alternates")],
        HRESULT,
        "Alternates",
        (["in"], c_int, "RequestCount"),
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseAlternates)), "Alternates"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("Audio")],
        HRESULT,
        "Audio",
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["out", "retval"], POINTER(POINTER(ISpeechMemoryStream)), "Stream"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("SpeakAudio")],
        HRESULT,
        "SpeakAudio",
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["in", "optional"], SpeechVoiceSpeakFlags, "Flags", 0),
        (["out", "retval"], POINTER(c_int), "StreamNumber"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("SaveToMemory")],
        HRESULT,
        "SaveToMemory",
        (["out", "retval"], POINTER(VARIANT), "ResultBlock"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("DiscardResultInfo")],
        HRESULT,
        "DiscardResultInfo",
        (["in"], SpeechDiscardType, "ValueTypes"),
    ),
]
################################################################
## code template for ISpeechRecoResult implementation
##class ISpeechRecoResult_Impl(object):
##    @property
##    def RecoContext(self):
##        'RecoContext'
##        #return RecoContext
##
##    @property
##    def Times(self):
##        'Times'
##        #return Times
##
##    @property
##    def AudioFormat(self, Format):
##        'AudioFormat'
##        #return
##
##    @property
##    def PhraseInfo(self):
##        'PhraseInfo'
##        #return PhraseInfo
##
##    def Alternates(self, RequestCount, StartElement, Elements):
##        'Alternates'
##        #return Alternates
##
##    def Audio(self, StartElement, Elements):
##        'Audio'
##        #return Stream
##
##    def SpeakAudio(self, StartElement, Elements, Flags):
##        'SpeakAudio'
##        #return StreamNumber
##
##    def SaveToMemory(self):
##        'SaveToMemory'
##        #return ResultBlock
##
##    def DiscardResultInfo(self, ValueTypes):
##        'DiscardResultInfo'
##        #return
##


# values for enumeration 'DISPID_SpeechAudioFormat'
DISPID_SAFType = 1
DISPID_SAFGuid = 2
DISPID_SAFGetWaveFormatEx = 3
DISPID_SAFSetWaveFormatEx = 4
DISPID_SpeechAudioFormat = c_int  # enum

# values for enumeration 'SpeechWordPronounceable'
SWPUnknownWordUnpronounceable = 0
SWPUnknownWordPronounceable = 1
SWPKnownWordPronounceable = 2
SpeechWordPronounceable = c_int  # enum

# values for enumeration 'DISPID_SpeechCustomStream'
DISPID_SCSBaseStream = 100
DISPID_SpeechCustomStream = c_int  # enum


class SpMMAudioOut(CoClass):
    "SpMMAudioOut Class"
    _reg_clsid_ = GUID("{A8C680EB-3D32-11D2-9EE7-00C04F797396}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpeechAudio(ISpeechBaseStream):
    _case_insensitive_ = True
    "ISpeechAudio Interface"
    _iid_ = GUID("{CFF8E175-019E-11D3-A08E-00C04F8EF9B5}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpeechMMSysAudio(ISpeechAudio):
    _case_insensitive_ = True
    "ISpeechMMSysAudio Interface"
    _iid_ = GUID("{3C76AF6D-1FD7-4831-81D1-3B71D5A13C44}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpNotifySource(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpNotifySource Interface"
    _iid_ = GUID("{5EFF4AEF-8487-11D2-961C-00C04F8EE628}")
    _idlflags_ = ["restricted"]


class ISpEventSource(ISpNotifySource):
    _case_insensitive_ = True
    "ISpEventSource Interface"
    _iid_ = GUID("{BE7A9CCE-5F9E-11D2-960F-00C04F8EE628}")
    _idlflags_ = ["restricted"]


class ISpEventSink(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpEventSink Interface"
    _iid_ = GUID("{BE7A9CC9-5F9E-11D2-960F-00C04F8EE628}")
    _idlflags_ = ["restricted"]


class ISpObjectWithToken(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpObjectWithToken Interface"
    _iid_ = GUID("{5B559F40-E952-11D2-BB91-00C04F8EE6C0}")
    _idlflags_ = ["restricted"]


class ISpMMSysAudio(ISpAudio):
    _case_insensitive_ = True
    "ISpMMSysAudio Interface"
    _iid_ = GUID("{15806F6E-1D70-4B48-98E6-3B1A007509AB}")
    _idlflags_ = ["restricted"]


SpMMAudioOut._com_interfaces_ = [
    ISpeechMMSysAudio,
    ISpEventSource,
    ISpEventSink,
    ISpObjectWithToken,
    ISpMMSysAudio,
]


class SpStream(CoClass):
    "SpStream Class"
    _reg_clsid_ = GUID("{715D9C59-4442-11D2-9605-00C04F8EE628}")
    _idlflags_ = ["hidden", "restricted"]
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpStream(ISpStreamFormat):
    _case_insensitive_ = True
    "ISpStream Interface"
    _iid_ = GUID("{12E3CCA9-7518-44C5-A5E7-BA5A79CB929E}")
    _idlflags_ = ["restricted"]


SpStream._com_interfaces_ = [ISpStream]


# values for enumeration 'SPFILEMODE'
SPFM_OPEN_READONLY = 0
SPFM_OPEN_READWRITE = 1
SPFM_CREATE = 2
SPFM_CREATE_ALWAYS = 3
SPFM_NUM_MODES = 4
SPFILEMODE = c_int  # enum
ISpStream._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetBaseStream",
        (["in"], POINTER(IStream), "pStream"),
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "rguidFormat",
        ),
        (["in"], POINTER(WAVEFORMATEX), "pWaveFormatEx"),
    ),
    COMMETHOD(
        [], HRESULT, "GetBaseStream", (["out"], POINTER(POINTER(IStream)), "ppStream")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "BindToFile",
        (["in"], WSTRING, "pszFileName"),
        (["in"], SPFILEMODE, "eMode"),
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pFormatId",
        ),
        ([], POINTER(WAVEFORMATEX), "pWaveFormatEx"),
        (["in"], c_ulonglong, "ullEventInterest"),
    ),
    COMMETHOD([], HRESULT, "Close"),
]
################################################################
## code template for ISpStream implementation
##class ISpStream_Impl(object):
##    def SetBaseStream(self, pStream, rguidFormat, pWaveFormatEx):
##        '-no docstring-'
##        #return
##
##    def GetBaseStream(self):
##        '-no docstring-'
##        #return ppStream
##
##    def BindToFile(self, pszFileName, eMode, pFormatId, pWaveFormatEx, ullEventInterest):
##        '-no docstring-'
##        #return
##
##    def Close(self):
##        '-no docstring-'
##        #return
##


# values for enumeration 'DISPID_SpeechObjectTokenCategory'
DISPID_SOTCId = 1
DISPID_SOTCDefault = 2
DISPID_SOTCSetId = 3
DISPID_SOTCGetDataKey = 4
DISPID_SOTCEnumerateTokens = 5
DISPID_SpeechObjectTokenCategory = c_int  # enum

# values for enumeration 'SPVPRIORITY'
SPVPRI_NORMAL = 0
SPVPRI_ALERT = 1
SPVPRI_OVER = 2
SPVPRIORITY = c_int  # enum

# values for enumeration 'DISPID_SpeechRecoContext'
DISPID_SRCRecognizer = 1
DISPID_SRCAudioInInterferenceStatus = 2
DISPID_SRCRequestedUIType = 3
DISPID_SRCVoice = 4
DISPID_SRAllowVoiceFormatMatchingOnNextSet = 5
DISPID_SRCVoicePurgeEvent = 6
DISPID_SRCEventInterests = 7
DISPID_SRCCmdMaxAlternates = 8
DISPID_SRCState = 9
DISPID_SRCRetainedAudio = 10
DISPID_SRCRetainedAudioFormat = 11
DISPID_SRCPause = 12
DISPID_SRCResume = 13
DISPID_SRCCreateGrammar = 14
DISPID_SRCCreateResultFromMemory = 15
DISPID_SRCBookmark = 16
DISPID_SRCSetAdaptationData = 17
DISPID_SpeechRecoContext = c_int  # enum

# values for enumeration 'DISPID_SpeechMemoryStream'
DISPID_SMSSetData = 100
DISPID_SMSGetData = 101
DISPID_SpeechMemoryStream = c_int  # enum
ISpeechRecoResultTimes._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("StreamTime"), "propget"],
        HRESULT,
        "StreamTime",
        (["out", "retval"], POINTER(VARIANT), "Time"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Length"), "propget"],
        HRESULT,
        "Length",
        (["out", "retval"], POINTER(VARIANT), "Length"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("TickCount"), "propget"],
        HRESULT,
        "TickCount",
        (["out", "retval"], POINTER(c_int), "TickCount"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Start"), "propget"],
        HRESULT,
        "OffsetFromStart",
        (["out", "retval"], POINTER(VARIANT), "OffsetFromStart"),
    ),
]
################################################################
## code template for ISpeechRecoResultTimes implementation
##class ISpeechRecoResultTimes_Impl(object):
##    @property
##    def StreamTime(self):
##        'StreamTime'
##        #return Time
##
##    @property
##    def Length(self):
##        'Length'
##        #return Length
##
##    @property
##    def TickCount(self):
##        'TickCount'
##        #return TickCount
##
##    @property
##    def OffsetFromStart(self):
##        'Start'
##        #return OffsetFromStart
##


# values for enumeration 'SPEVENTENUM'
SPEI_UNDEFINED = 0
SPEI_START_INPUT_STREAM = 1
SPEI_END_INPUT_STREAM = 2
SPEI_VOICE_CHANGE = 3
SPEI_TTS_BOOKMARK = 4
SPEI_WORD_BOUNDARY = 5
SPEI_PHONEME = 6
SPEI_SENTENCE_BOUNDARY = 7
SPEI_VISEME = 8
SPEI_TTS_AUDIO_LEVEL = 9
SPEI_TTS_PRIVATE = 15
SPEI_MIN_TTS = 1
SPEI_MAX_TTS = 15
SPEI_END_SR_STREAM = 34
SPEI_SOUND_START = 35
SPEI_SOUND_END = 36
SPEI_PHRASE_START = 37
SPEI_RECOGNITION = 38
SPEI_HYPOTHESIS = 39
SPEI_SR_BOOKMARK = 40
SPEI_PROPERTY_NUM_CHANGE = 41
SPEI_PROPERTY_STRING_CHANGE = 42
SPEI_FALSE_RECOGNITION = 43
SPEI_INTERFERENCE = 44
SPEI_REQUEST_UI = 45
SPEI_RECO_STATE_CHANGE = 46
SPEI_ADAPTATION = 47
SPEI_START_SR_STREAM = 48
SPEI_RECO_OTHER_CONTEXT = 49
SPEI_SR_AUDIO_LEVEL = 50
SPEI_SR_RETAINEDAUDIO = 51
SPEI_SR_PRIVATE = 52
SPEI_ACTIVE_CATEGORY_CHANGED = 53
SPEI_RESERVED5 = 54
SPEI_RESERVED6 = 55
SPEI_MIN_SR = 34
SPEI_MAX_SR = 55
SPEI_RESERVED1 = 30
SPEI_RESERVED2 = 33
SPEI_RESERVED3 = 63
SPEVENTENUM = c_int  # enum

# values for enumeration 'DISPIDSPRG'
DISPID_SRGId = 1
DISPID_SRGRecoContext = 2
DISPID_SRGState = 3
DISPID_SRGRules = 4
DISPID_SRGReset = 5
DISPID_SRGCommit = 6
DISPID_SRGCmdLoadFromFile = 7
DISPID_SRGCmdLoadFromObject = 8
DISPID_SRGCmdLoadFromResource = 9
DISPID_SRGCmdLoadFromMemory = 10
DISPID_SRGCmdLoadFromProprietaryGrammar = 11
DISPID_SRGCmdSetRuleState = 12
DISPID_SRGCmdSetRuleIdState = 13
DISPID_SRGDictationLoad = 14
DISPID_SRGDictationUnload = 15
DISPID_SRGDictationSetState = 16
DISPID_SRGSetWordSequenceData = 17
DISPID_SRGSetTextSelection = 18
DISPID_SRGIsPronounceable = 19
DISPIDSPRG = c_int  # enum


class ISpProperties(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpProperties Interface"
    _iid_ = GUID("{5B4FB971-B115-4DE1-AD97-E482E3BF6EE4}")
    _idlflags_ = ["restricted"]


class ISpRecognizer(ISpProperties):
    _case_insensitive_ = True
    "ISpRecognizer Interface"
    _iid_ = GUID("{C2B5F241-DAA0-4507-9E16-5A1EAA2B7A5C}")
    _idlflags_ = ["restricted"]


ISpProperties._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetPropertyNum",
        (["in"], WSTRING, "pName"),
        (["in"], c_int, "lValue"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetPropertyNum",
        (["in"], WSTRING, "pName"),
        (["out"], POINTER(c_int), "plValue"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetPropertyString",
        (["in"], WSTRING, "pName"),
        (["in"], WSTRING, "pValue"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetPropertyString",
        (["in"], WSTRING, "pName"),
        (["out"], POINTER(WSTRING), "ppCoMemValue"),
    ),
]
################################################################
## code template for ISpProperties implementation
##class ISpProperties_Impl(object):
##    def SetPropertyNum(self, pName, lValue):
##        '-no docstring-'
##        #return
##
##    def GetPropertyNum(self, pName):
##        '-no docstring-'
##        #return plValue
##
##    def SetPropertyString(self, pName, pValue):
##        '-no docstring-'
##        #return
##
##    def GetPropertyString(self, pName):
##        '-no docstring-'
##        #return ppCoMemValue
##


class ISpRecoContext(ISpEventSource):
    _case_insensitive_ = True
    "ISpRecoContext Interface"
    _iid_ = GUID("{F740A62F-7C15-489E-8234-940A33D9272D}")
    _idlflags_ = ["restricted"]


# values for enumeration 'SPRECOSTATE'
SPRST_INACTIVE = 0
SPRST_ACTIVE = 1
SPRST_ACTIVE_ALWAYS = 2
SPRST_INACTIVE_WITH_PURGE = 3
SPRST_NUM_STATES = 4
SPRECOSTATE = c_int  # enum


class SPRECOGNIZERSTATUS(Structure):
    pass


# values for enumeration 'SPWAVEFORMATTYPE'
SPWF_INPUT = 0
SPWF_SRENGINE = 1
SPWAVEFORMATTYPE = c_int  # enum
SPSTREAMFORMATTYPE = SPWAVEFORMATTYPE


class ISpPhrase(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpPhrase Interface"
    _iid_ = GUID("{1A5C0354-B621-4B5A-8791-D306ED379E53}")
    _idlflags_ = ["restricted"]


ISpRecognizer._methods_ = [
    COMMETHOD(
        [], HRESULT, "SetRecognizer", (["in"], POINTER(ISpObjectToken), "pRecognizer")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetRecognizer",
        (["out"], POINTER(POINTER(ISpObjectToken)), "ppRecognizer"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetInput",
        (["in"], POINTER(IUnknown), "pUnkInput"),
        (["in"], c_int, "fAllowFormatChanges"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetInputObjectToken",
        (["out"], POINTER(POINTER(ISpObjectToken)), "ppToken"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetInputStream",
        (["out"], POINTER(POINTER(ISpStreamFormat)), "ppStream"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "CreateRecoContext",
        (["out"], POINTER(POINTER(ISpRecoContext)), "ppNewCtxt"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetRecoProfile",
        (["out"], POINTER(POINTER(ISpObjectToken)), "ppToken"),
    ),
    COMMETHOD(
        [], HRESULT, "SetRecoProfile", (["in"], POINTER(ISpObjectToken), "pToken")
    ),
    COMMETHOD([], HRESULT, "IsSharedInstance"),
    COMMETHOD([], HRESULT, "GetRecoState", (["out"], POINTER(SPRECOSTATE), "pState")),
    COMMETHOD([], HRESULT, "SetRecoState", (["in"], SPRECOSTATE, "NewState")),
    COMMETHOD(
        [], HRESULT, "GetStatus", (["out"], POINTER(SPRECOGNIZERSTATUS), "pStatus")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetFormat",
        (["in"], SPSTREAMFORMATTYPE, "WaveFormatType"),
        (
            ["out"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pFormatId",
        ),
        (["out"], POINTER(POINTER(WAVEFORMATEX)), "ppCoMemWFEX"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "IsUISupported",
        (["in"], WSTRING, "pszTypeOfUI"),
        (["in"], c_void_p, "pvExtraData"),
        (["in"], c_ulong, "cbExtraData"),
        (["out"], POINTER(c_int), "pfSupported"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "DisplayUI",
        (["in"], wireHWND, "hWndParent"),
        (["in"], WSTRING, "pszTitle"),
        (["in"], WSTRING, "pszTypeOfUI"),
        (["in"], c_void_p, "pvExtraData"),
        (["in"], c_ulong, "cbExtraData"),
    ),
    COMMETHOD(
        [], HRESULT, "EmulateRecognition", (["in"], POINTER(ISpPhrase), "pPhrase")
    ),
]
################################################################
## code template for ISpRecognizer implementation
##class ISpRecognizer_Impl(object):
##    def SetRecognizer(self, pRecognizer):
##        '-no docstring-'
##        #return
##
##    def GetRecognizer(self):
##        '-no docstring-'
##        #return ppRecognizer
##
##    def SetInput(self, pUnkInput, fAllowFormatChanges):
##        '-no docstring-'
##        #return
##
##    def GetInputObjectToken(self):
##        '-no docstring-'
##        #return ppToken
##
##    def GetInputStream(self):
##        '-no docstring-'
##        #return ppStream
##
##    def CreateRecoContext(self):
##        '-no docstring-'
##        #return ppNewCtxt
##
##    def GetRecoProfile(self):
##        '-no docstring-'
##        #return ppToken
##
##    def SetRecoProfile(self, pToken):
##        '-no docstring-'
##        #return
##
##    def IsSharedInstance(self):
##        '-no docstring-'
##        #return
##
##    def GetRecoState(self):
##        '-no docstring-'
##        #return pState
##
##    def SetRecoState(self, NewState):
##        '-no docstring-'
##        #return
##
##    def GetStatus(self):
##        '-no docstring-'
##        #return pStatus
##
##    def GetFormat(self, WaveFormatType):
##        '-no docstring-'
##        #return pFormatId, ppCoMemWFEX
##
##    def IsUISupported(self, pszTypeOfUI, pvExtraData, cbExtraData):
##        '-no docstring-'
##        #return pfSupported
##
##    def DisplayUI(self, hWndParent, pszTitle, pszTypeOfUI, pvExtraData, cbExtraData):
##        '-no docstring-'
##        #return
##
##    def EmulateRecognition(self, pPhrase):
##        '-no docstring-'
##        #return
##


# values for enumeration 'SpeechRecoEvents'
SREStreamEnd = 1
SRESoundStart = 2
SRESoundEnd = 4
SREPhraseStart = 8
SRERecognition = 16
SREHypothesis = 32
SREBookmark = 64
SREPropertyNumChange = 128
SREPropertyStringChange = 256
SREFalseRecognition = 512
SREInterference = 1024
SRERequestUI = 2048
SREStateChange = 4096
SREAdaptation = 8192
SREStreamStart = 16384
SRERecoOtherContext = 32768
SREAudioLevel = 65536
SREPrivate = 262144
SREAllEvents = 393215
SpeechRecoEvents = c_int  # enum

# values for enumeration 'DISPID_SpeechAudioStatus'
DISPID_SASFreeBufferSpace = 1
DISPID_SASNonBlockingIO = 2
DISPID_SASState = 3
DISPID_SASCurrentSeekPosition = 4
DISPID_SASCurrentDevicePosition = 5
DISPID_SpeechAudioStatus = c_int  # enum

# values for enumeration 'SpeechDisplayAttributes'
SDA_No_Trailing_Space = 0
SDA_One_Trailing_Space = 2
SDA_Two_Trailing_Spaces = 4
SDA_Consume_Leading_Spaces = 8
SpeechDisplayAttributes = c_int  # enum
ISpeechPhraseInfo._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("LanguageId"), "propget"],
        HRESULT,
        "LanguageId",
        (["out", "retval"], POINTER(c_int), "LanguageId"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("GrammarId"), "propget"],
        HRESULT,
        "GrammarId",
        (["out", "retval"], POINTER(VARIANT), "GrammarId"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("StartTime"), "propget"],
        HRESULT,
        "StartTime",
        (["out", "retval"], POINTER(VARIANT), "StartTime"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AudioStreamPosition"), "propget"],
        HRESULT,
        "AudioStreamPosition",
        (["out", "retval"], POINTER(VARIANT), "AudioStreamPosition"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("AudioSizeBytes"), "propget"],
        HRESULT,
        "AudioSizeBytes",
        (["out", "retval"], POINTER(c_int), "pAudioSizeBytes"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("RetainedSizeBytes"), "propget"],
        HRESULT,
        "RetainedSizeBytes",
        (["out", "retval"], POINTER(c_int), "RetainedSizeBytes"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("AudioSizeTime"), "propget"],
        HRESULT,
        "AudioSizeTime",
        (["out", "retval"], POINTER(c_int), "AudioSizeTime"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("Rule"), "propget"],
        HRESULT,
        "Rule",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseRule)), "Rule"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("Properties"), "propget"],
        HRESULT,
        "Properties",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseProperties)), "Properties"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("Elements"), "propget"],
        HRESULT,
        "Elements",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseElements)), "Elements"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("Replacements"), "propget"],
        HRESULT,
        "Replacements",
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechPhraseReplacements)),
            "Replacements",
        ),
    ),
    COMMETHOD(
        [dispid(12), helpstring("EngineId"), "propget"],
        HRESULT,
        "EngineId",
        (["out", "retval"], POINTER(BSTR), "EngineIdGuid"),
    ),
    COMMETHOD(
        [dispid(13), helpstring("EnginePrivateData"), "propget"],
        HRESULT,
        "EnginePrivateData",
        (["out", "retval"], POINTER(VARIANT), "PrivateData"),
    ),
    COMMETHOD(
        [dispid(14), helpstring("SaveToMemory")],
        HRESULT,
        "SaveToMemory",
        (["out", "retval"], POINTER(VARIANT), "PhraseBlock"),
    ),
    COMMETHOD(
        [dispid(15), helpstring("GetText")],
        HRESULT,
        "GetText",
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["in", "optional"], VARIANT_BOOL, "UseReplacements", True),
        (["out", "retval"], POINTER(BSTR), "Text"),
    ),
    COMMETHOD(
        [dispid(16), helpstring("DisplayAttributes")],
        HRESULT,
        "GetDisplayAttributes",
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["in", "optional"], VARIANT_BOOL, "UseReplacements", True),
        (["out", "retval"], POINTER(SpeechDisplayAttributes), "DisplayAttributes"),
    ),
]
################################################################
## code template for ISpeechPhraseInfo implementation
##class ISpeechPhraseInfo_Impl(object):
##    @property
##    def LanguageId(self):
##        'LanguageId'
##        #return LanguageId
##
##    @property
##    def GrammarId(self):
##        'GrammarId'
##        #return GrammarId
##
##    @property
##    def StartTime(self):
##        'StartTime'
##        #return StartTime
##
##    @property
##    def AudioStreamPosition(self):
##        'AudioStreamPosition'
##        #return AudioStreamPosition
##
##    @property
##    def AudioSizeBytes(self):
##        'AudioSizeBytes'
##        #return pAudioSizeBytes
##
##    @property
##    def RetainedSizeBytes(self):
##        'RetainedSizeBytes'
##        #return RetainedSizeBytes
##
##    @property
##    def AudioSizeTime(self):
##        'AudioSizeTime'
##        #return AudioSizeTime
##
##    @property
##    def Rule(self):
##        'Rule'
##        #return Rule
##
##    @property
##    def Properties(self):
##        'Properties'
##        #return Properties
##
##    @property
##    def Elements(self):
##        'Elements'
##        #return Elements
##
##    @property
##    def Replacements(self):
##        'Replacements'
##        #return Replacements
##
##    @property
##    def EngineId(self):
##        'EngineId'
##        #return EngineIdGuid
##
##    @property
##    def EnginePrivateData(self):
##        'EnginePrivateData'
##        #return PrivateData
##
##    def SaveToMemory(self):
##        'SaveToMemory'
##        #return PhraseBlock
##
##    def GetText(self, StartElement, Elements, UseReplacements):
##        'GetText'
##        #return Text
##
##    def GetDisplayAttributes(self, StartElement, Elements, UseReplacements):
##        'DisplayAttributes'
##        #return DisplayAttributes
##


class ISpeechPhraseAlternate(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseAlternate Interface"
    _iid_ = GUID("{27864A2A-2B9F-4CB8-92D3-0D2722FD1E73}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechPhraseAlternates._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechPhraseAlternate)),
            "PhraseAlternate",
        ),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the alternates"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechPhraseAlternates implementation
##class ISpeechPhraseAlternates_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return PhraseAlternate
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the alternates'
##        #return EnumVARIANT
##


# values for enumeration 'DISPID_SpeechAudioBufferInfo'
DISPID_SABIMinNotification = 1
DISPID_SABIBufferSize = 2
DISPID_SABIEventBias = 3
DISPID_SpeechAudioBufferInfo = c_int  # enum

# values for enumeration 'DISPID_SpeechFileStream'
DISPID_SFSOpen = 100
DISPID_SFSClose = 101
DISPID_SpeechFileStream = c_int  # enum


class SpSharedRecoContext(CoClass):
    "SpSharedRecoContext Class"
    _reg_clsid_ = GUID("{47206204-5ECA-11D2-960F-00C04F8EE628}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpRecoContext2(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpRecoContext2 Interface"
    _iid_ = GUID("{BEAD311C-52FF-437F-9464-6B21054CA73D}")
    _idlflags_ = ["restricted"]


class ISpPhoneticAlphabetSelection(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpPhoneticAlphabetSelection Interface"
    _iid_ = GUID("{B2745EFD-42CE-48CA-81F1-A96E02538A90}")
    _idlflags_ = ["restricted"]


class _ISpeechRecoContextEvents(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    _iid_ = GUID("{7B8FCB42-0E9D-4F00-A048-7B04D6179D3D}")
    _idlflags_ = []
    _methods_ = []


SpSharedRecoContext._com_interfaces_ = [
    ISpeechRecoContext,
    ISpRecoContext,
    ISpRecoContext2,
    ISpPhoneticAlphabetSelection,
]
SpSharedRecoContext._outgoing_interfaces_ = [_ISpeechRecoContextEvents]


# values for enumeration 'DISPID_SpeechGrammarRuleStateTransitions'
DISPID_SGRSTsCount = 1
DISPID_SGRSTsItem = 0
DISPID_SGRSTs_NewEnum = -4
DISPID_SpeechGrammarRuleStateTransitions = c_int  # enum


class ISpeechXMLRecoResult(ISpeechRecoResult):
    _case_insensitive_ = True
    "ISpeechXMLRecoResult Interface"
    _iid_ = GUID("{AAEC54AF-8F85-4924-944D-B79D39D72E19}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SPXMLRESULTOPTIONS'
SPXRO_SML = 0
SPXRO_Alternates_SML = 1
SPXMLRESULTOPTIONS = c_int  # enum
ISpeechXMLRecoResult._methods_ = [
    COMMETHOD(
        [dispid(10), helpstring("GetXMLResult")],
        HRESULT,
        "GetXMLResult",
        (["in"], SPXMLRESULTOPTIONS, "Options"),
        (["out", "retval"], POINTER(BSTR), "pResult"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("GetXMLErrorInfo")],
        HRESULT,
        "GetXMLErrorInfo",
        (["out"], POINTER(c_int), "LineNumber"),
        (["out"], POINTER(BSTR), "ScriptLine"),
        (["out"], POINTER(BSTR), "Source"),
        (["out"], POINTER(BSTR), "Description"),
        (["out"], POINTER(c_int), "ResultCode"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "IsError"),
    ),
]
################################################################
## code template for ISpeechXMLRecoResult implementation
##class ISpeechXMLRecoResult_Impl(object):
##    def GetXMLResult(self, Options):
##        'GetXMLResult'
##        #return pResult
##
##    def GetXMLErrorInfo(self):
##        'GetXMLErrorInfo'
##        #return LineNumber, ScriptLine, Source, Description, ResultCode, IsError
##


class SpVoice(CoClass):
    "SpVoice Class"
    _reg_clsid_ = GUID("{96749377-3391-11D2-9EE3-00C04F797396}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpeechVoice(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch):
    _case_insensitive_ = True
    "ISpeechVoice Interface"
    _iid_ = GUID("{269316D8-57BD-11D2-9EEE-00C04F797396}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpVoice(ISpEventSource):
    _case_insensitive_ = True
    "ISpVoice Interface"
    _iid_ = GUID("{6C44DF74-72B9-4992-A1EC-EF996E0422D4}")
    _idlflags_ = ["restricted"]


class _ISpeechVoiceEvents(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    _iid_ = GUID("{A372ACD1-3BEF-4BBD-8FFB-CB3E2B416AF8}")
    _idlflags_ = []
    _methods_ = []


SpVoice._com_interfaces_ = [ISpeechVoice, ISpVoice, ISpPhoneticAlphabetSelection]
SpVoice._outgoing_interfaces_ = [_ISpeechVoiceEvents]


class ISpNotifySink(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpNotifySink Interface"
    _iid_ = GUID("{259684DC-37C3-11D2-9603-00C04F8EE628}")
    _idlflags_ = ["restricted"]


ISpNotifySource._methods_ = [
    COMMETHOD(
        [], HRESULT, "SetNotifySink", (["in"], POINTER(ISpNotifySink), "pNotifySink")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetNotifyWindowMessage",
        (["in"], wireHWND, "hWnd"),
        (["in"], c_uint, "Msg"),
        (["in"], UINT_PTR, "wParam"),
        (["in"], LONG_PTR, "lParam"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetNotifyCallbackFunction",
        (["in"], POINTER(c_void_p), "pfnCallback"),
        (["in"], UINT_PTR, "wParam"),
        (["in"], LONG_PTR, "lParam"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetNotifyCallbackInterface",
        (["in"], POINTER(c_void_p), "pSpCallback"),
        (["in"], UINT_PTR, "wParam"),
        (["in"], LONG_PTR, "lParam"),
    ),
    COMMETHOD([], HRESULT, "SetNotifyWin32Event"),
    COMMETHOD([], HRESULT, "WaitForNotifyEvent", (["in"], c_ulong, "dwMilliseconds")),
    COMMETHOD([], c_void_p, "GetNotifyEventHandle"),
]
################################################################
## code template for ISpNotifySource implementation
##class ISpNotifySource_Impl(object):
##    def SetNotifySink(self, pNotifySink):
##        '-no docstring-'
##        #return
##
##    def SetNotifyWindowMessage(self, hWnd, Msg, wParam, lParam):
##        '-no docstring-'
##        #return
##
##    def SetNotifyCallbackFunction(self, pfnCallback, wParam, lParam):
##        '-no docstring-'
##        #return
##
##    def SetNotifyCallbackInterface(self, pSpCallback, wParam, lParam):
##        '-no docstring-'
##        #return
##
##    def SetNotifyWin32Event(self):
##        '-no docstring-'
##        #return
##
##    def WaitForNotifyEvent(self, dwMilliseconds):
##        '-no docstring-'
##        #return
##
##    def GetNotifyEventHandle(self):
##        '-no docstring-'
##        #return
##


class SPEVENT(Structure):
    pass


class SPEVENTSOURCEINFO(Structure):
    pass


ISpEventSource._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetInterest",
        (["in"], c_ulonglong, "ullEventInterest"),
        (["in"], c_ulonglong, "ullQueuedInterest"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetEvents",
        (["in"], c_ulong, "ulCount"),
        (["out"], POINTER(SPEVENT), "pEventArray"),
        (["out"], POINTER(c_ulong), "pulFetched"),
    ),
    COMMETHOD([], HRESULT, "GetInfo", (["out"], POINTER(SPEVENTSOURCEINFO), "pInfo")),
]
################################################################
## code template for ISpEventSource implementation
##class ISpEventSource_Impl(object):
##    def SetInterest(self, ullEventInterest, ullQueuedInterest):
##        '-no docstring-'
##        #return
##
##    def GetEvents(self, ulCount):
##        '-no docstring-'
##        #return pEventArray, pulFetched
##
##    def GetInfo(self):
##        '-no docstring-'
##        #return pInfo
##

ISpVoice._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetOutput",
        (["in"], POINTER(IUnknown), "pUnkOutput"),
        (["in"], c_int, "fAllowFormatChanges"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetOutputObjectToken",
        (["out"], POINTER(POINTER(ISpObjectToken)), "ppObjectToken"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetOutputStream",
        (["out"], POINTER(POINTER(ISpStreamFormat)), "ppStream"),
    ),
    COMMETHOD([], HRESULT, "Pause"),
    COMMETHOD([], HRESULT, "Resume"),
    COMMETHOD([], HRESULT, "SetVoice", (["in"], POINTER(ISpObjectToken), "pToken")),
    COMMETHOD(
        [], HRESULT, "GetVoice", (["out"], POINTER(POINTER(ISpObjectToken)), "ppToken")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "Speak",
        (["in"], WSTRING, "pwcs"),
        (["in"], c_ulong, "dwFlags"),
        (["out"], POINTER(c_ulong), "pulStreamNumber"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SpeakStream",
        (["in"], POINTER(IStream), "pStream"),
        (["in"], c_ulong, "dwFlags"),
        (["out"], POINTER(c_ulong), "pulStreamNumber"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetStatus",
        (["out"], POINTER(SPVOICESTATUS), "pStatus"),
        (["out"], POINTER(WSTRING), "ppszLastBookmark"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "Skip",
        (["in"], WSTRING, "pItemType"),
        (["in"], c_int, "lNumItems"),
        (["out"], POINTER(c_ulong), "pulNumSkipped"),
    ),
    COMMETHOD([], HRESULT, "SetPriority", (["in"], SPVPRIORITY, "ePriority")),
    COMMETHOD(
        [], HRESULT, "GetPriority", (["out"], POINTER(SPVPRIORITY), "pePriority")
    ),
    COMMETHOD([], HRESULT, "SetAlertBoundary", (["in"], SPEVENTENUM, "eBoundary")),
    COMMETHOD(
        [], HRESULT, "GetAlertBoundary", (["out"], POINTER(SPEVENTENUM), "peBoundary")
    ),
    COMMETHOD([], HRESULT, "SetRate", (["in"], c_int, "RateAdjust")),
    COMMETHOD([], HRESULT, "GetRate", (["out"], POINTER(c_int), "pRateAdjust")),
    COMMETHOD([], HRESULT, "SetVolume", (["in"], c_ushort, "usVolume")),
    COMMETHOD([], HRESULT, "GetVolume", (["out"], POINTER(c_ushort), "pusVolume")),
    COMMETHOD([], HRESULT, "WaitUntilDone", (["in"], c_ulong, "msTimeout")),
    COMMETHOD([], HRESULT, "SetSyncSpeakTimeout", (["in"], c_ulong, "msTimeout")),
    COMMETHOD(
        [], HRESULT, "GetSyncSpeakTimeout", (["out"], POINTER(c_ulong), "pmsTimeout")
    ),
    COMMETHOD([], c_void_p, "SpeakCompleteEvent"),
    COMMETHOD(
        [],
        HRESULT,
        "IsUISupported",
        (["in"], WSTRING, "pszTypeOfUI"),
        (["in"], c_void_p, "pvExtraData"),
        (["in"], c_ulong, "cbExtraData"),
        (["out"], POINTER(c_int), "pfSupported"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "DisplayUI",
        (["in"], wireHWND, "hWndParent"),
        (["in"], WSTRING, "pszTitle"),
        (["in"], WSTRING, "pszTypeOfUI"),
        (["in"], c_void_p, "pvExtraData"),
        (["in"], c_ulong, "cbExtraData"),
    ),
]
################################################################
## code template for ISpVoice implementation
##class ISpVoice_Impl(object):
##    def SetOutput(self, pUnkOutput, fAllowFormatChanges):
##        '-no docstring-'
##        #return
##
##    def GetOutputObjectToken(self):
##        '-no docstring-'
##        #return ppObjectToken
##
##    def GetOutputStream(self):
##        '-no docstring-'
##        #return ppStream
##
##    def Pause(self):
##        '-no docstring-'
##        #return
##
##    def Resume(self):
##        '-no docstring-'
##        #return
##
##    def SetVoice(self, pToken):
##        '-no docstring-'
##        #return
##
##    def GetVoice(self):
##        '-no docstring-'
##        #return ppToken
##
##    def Speak(self, pwcs, dwFlags):
##        '-no docstring-'
##        #return pulStreamNumber
##
##    def SpeakStream(self, pStream, dwFlags):
##        '-no docstring-'
##        #return pulStreamNumber
##
##    def GetStatus(self):
##        '-no docstring-'
##        #return pStatus, ppszLastBookmark
##
##    def Skip(self, pItemType, lNumItems):
##        '-no docstring-'
##        #return pulNumSkipped
##
##    def SetPriority(self, ePriority):
##        '-no docstring-'
##        #return
##
##    def GetPriority(self):
##        '-no docstring-'
##        #return pePriority
##
##    def SetAlertBoundary(self, eBoundary):
##        '-no docstring-'
##        #return
##
##    def GetAlertBoundary(self):
##        '-no docstring-'
##        #return peBoundary
##
##    def SetRate(self, RateAdjust):
##        '-no docstring-'
##        #return
##
##    def GetRate(self):
##        '-no docstring-'
##        #return pRateAdjust
##
##    def SetVolume(self, usVolume):
##        '-no docstring-'
##        #return
##
##    def GetVolume(self):
##        '-no docstring-'
##        #return pusVolume
##
##    def WaitUntilDone(self, msTimeout):
##        '-no docstring-'
##        #return
##
##    def SetSyncSpeakTimeout(self, msTimeout):
##        '-no docstring-'
##        #return
##
##    def GetSyncSpeakTimeout(self):
##        '-no docstring-'
##        #return pmsTimeout
##
##    def SpeakCompleteEvent(self):
##        '-no docstring-'
##        #return
##
##    def IsUISupported(self, pszTypeOfUI, pvExtraData, cbExtraData):
##        '-no docstring-'
##        #return pfSupported
##
##    def DisplayUI(self, hWndParent, pszTitle, pszTypeOfUI, pvExtraData, cbExtraData):
##        '-no docstring-'
##        #return
##


class ISpNotifyTranslator(ISpNotifySink):
    _case_insensitive_ = True
    "ISpNotifyTranslator Interface"
    _iid_ = GUID("{ACA16614-5D3D-11D2-960E-00C04F8EE628}")
    _idlflags_ = ["restricted"]


ISpNotifySink._methods_ = [
    COMMETHOD([], HRESULT, "Notify"),
]
################################################################
## code template for ISpNotifySink implementation
##class ISpNotifySink_Impl(object):
##    def Notify(self):
##        '-no docstring-'
##        #return
##

ISpNotifyTranslator._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "InitWindowMessage",
        (["in"], wireHWND, "hWnd"),
        (["in"], c_uint, "Msg"),
        (["in"], UINT_PTR, "wParam"),
        (["in"], LONG_PTR, "lParam"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "InitCallback",
        (["in"], POINTER(c_void_p), "pfnCallback"),
        (["in"], UINT_PTR, "wParam"),
        (["in"], LONG_PTR, "lParam"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "InitSpNotifyCallback",
        (["in"], POINTER(c_void_p), "pSpCallback"),
        (["in"], UINT_PTR, "wParam"),
        (["in"], LONG_PTR, "lParam"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "InitWin32Event",
        (["in"], c_void_p, "hEvent"),
        (["in"], c_int, "fCloseHandleOnRelease"),
    ),
    COMMETHOD([], HRESULT, "Wait", (["in"], c_ulong, "dwMilliseconds")),
    COMMETHOD([], c_void_p, "GetEventHandle"),
]
################################################################
## code template for ISpNotifyTranslator implementation
##class ISpNotifyTranslator_Impl(object):
##    def InitWindowMessage(self, hWnd, Msg, wParam, lParam):
##        '-no docstring-'
##        #return
##
##    def InitCallback(self, pfnCallback, wParam, lParam):
##        '-no docstring-'
##        #return
##
##    def InitSpNotifyCallback(self, pSpCallback, wParam, lParam):
##        '-no docstring-'
##        #return
##
##    def InitWin32Event(self, hEvent, fCloseHandleOnRelease):
##        '-no docstring-'
##        #return
##
##    def Wait(self, dwMilliseconds):
##        '-no docstring-'
##        #return
##
##    def GetEventHandle(self):
##        '-no docstring-'
##        #return
##


# values for enumeration 'DISPID_SpeechPhraseRules'
DISPID_SPRulesCount = 1
DISPID_SPRulesItem = 0
DISPID_SPRules_NewEnum = -4
DISPID_SpeechPhraseRules = c_int  # enum


class SpNotifyTranslator(CoClass):
    "SpNotify"
    _reg_clsid_ = GUID("{E2AE5372-5D40-11D2-960E-00C04F8EE628}")
    _idlflags_ = ["hidden", "restricted"]
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpNotifyTranslator._com_interfaces_ = [ISpNotifyTranslator]


# values for enumeration 'DISPID_SpeechLexicon'
DISPID_SLGenerationId = 1
DISPID_SLGetWords = 2
DISPID_SLAddPronunciation = 3
DISPID_SLAddPronunciationByPhoneIds = 4
DISPID_SLRemovePronunciation = 5
DISPID_SLRemovePronunciationByPhoneIds = 6
DISPID_SLGetPronunciations = 7
DISPID_SLGetGenerationChange = 8
DISPID_SpeechLexicon = c_int  # enum


class SPPHRASE(Structure):
    pass


class SPSERIALIZEDPHRASE(Structure):
    pass


ISpPhrase._methods_ = [
    COMMETHOD(
        [], HRESULT, "GetPhrase", (["out"], POINTER(POINTER(SPPHRASE)), "ppCoMemPhrase")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetSerializedPhrase",
        (["out"], POINTER(POINTER(SPSERIALIZEDPHRASE)), "ppCoMemPhrase"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetText",
        (["in"], c_ulong, "ulStart"),
        (["in"], c_ulong, "ulCount"),
        (["in"], c_int, "fUseTextReplacements"),
        (["out"], POINTER(WSTRING), "ppszCoMemText"),
        (["out", "optional"], POINTER(c_ubyte), "pbDisplayAttributes"),
    ),
    COMMETHOD([], HRESULT, "Discard", (["in"], c_ulong, "dwValueTypes")),
]
################################################################
## code template for ISpPhrase implementation
##class ISpPhrase_Impl(object):
##    def GetPhrase(self):
##        '-no docstring-'
##        #return ppCoMemPhrase
##
##    def GetSerializedPhrase(self):
##        '-no docstring-'
##        #return ppCoMemPhrase
##
##    def GetText(self, ulStart, ulCount, fUseTextReplacements):
##        '-no docstring-'
##        #return ppszCoMemText, pbDisplayAttributes
##
##    def Discard(self, dwValueTypes):
##        '-no docstring-'
##        #return
##


# values for enumeration 'SpeechRecoContextState'
SRCS_Disabled = 0
SRCS_Enabled = 1
SpeechRecoContextState = c_int  # enum

# values for enumeration 'DISPID_SpeechLexiconProns'
DISPID_SLPsCount = 1
DISPID_SLPsItem = 0
DISPID_SLPs_NewEnum = -4
DISPID_SpeechLexiconProns = c_int  # enum


class SPWORDPRONUNCIATIONLIST(Structure):
    pass


class SPWORDPRONUNCIATION(Structure):
    pass


SPWORDPRONUNCIATIONLIST._fields_ = [
    ("ulSize", c_ulong),
    ("pvBuffer", POINTER(c_ubyte)),
    ("pFirstWordPronunciation", POINTER(SPWORDPRONUNCIATION)),
]
assert sizeof(SPWORDPRONUNCIATIONLIST) == 12, sizeof(SPWORDPRONUNCIATIONLIST)
assert alignment(SPWORDPRONUNCIATIONLIST) == 4, alignment(SPWORDPRONUNCIATIONLIST)

# values for enumeration 'DISPID_SpeechLexiconWords'
DISPID_SLWsCount = 1
DISPID_SLWsItem = 0
DISPID_SLWs_NewEnum = -4
DISPID_SpeechLexiconWords = c_int  # enum

# values for enumeration 'SpeechRetainedAudioOptions'
SRAONone = 0
SRAORetainAudio = 1
SpeechRetainedAudioOptions = c_int  # enum

# values for enumeration 'DISPID_SpeechLexiconWord'
DISPID_SLWLangId = 1
DISPID_SLWType = 2
DISPID_SLWWord = 3
DISPID_SLWPronunciations = 4
DISPID_SpeechLexiconWord = c_int  # enum


class SPPHRASERULE(Structure):
    pass


SPPHRASERULE._fields_ = [
    ("pszName", WSTRING),
    ("ulId", c_ulong),
    ("ulFirstElement", c_ulong),
    ("ulCountOfElements", c_ulong),
    ("pNextSibling", POINTER(SPPHRASERULE)),
    ("pFirstChild", POINTER(SPPHRASERULE)),
    ("SREngineConfidence", c_float),
    ("Confidence", c_char),
]
assert sizeof(SPPHRASERULE) == 32, sizeof(SPPHRASERULE)
assert alignment(SPPHRASERULE) == 4, alignment(SPPHRASERULE)


class SPPHRASEPROPERTY(Structure):
    pass


class SPPHRASEELEMENT(Structure):
    pass


class SPPHRASEREPLACEMENT(Structure):
    pass


class SPSEMANTICERRORINFO(Structure):
    pass


# values for enumeration 'SPSEMANTICFORMAT'
SPSMF_SAPI_PROPERTIES = 0
SPSMF_SRGS_SEMANTICINTERPRETATION_MS = 1
SPSMF_SRGS_SAPIPROPERTIES = 2
SPSMF_UPS = 4
SPSMF_SRGS_SEMANTICINTERPRETATION_W3C = 8
SPSEMANTICFORMAT = c_int  # enum
SPPHRASE._fields_ = [
    ("cbSize", c_ulong),
    ("LangId", c_ushort),
    ("wHomophoneGroupId", c_ushort),
    ("ullGrammarID", c_ulonglong),
    ("ftStartTime", c_ulonglong),
    ("ullAudioStreamPosition", c_ulonglong),
    ("ulAudioSizeBytes", c_ulong),
    ("ulRetainedSizeBytes", c_ulong),
    ("ulAudioSizeTime", c_ulong),
    ("Rule", SPPHRASERULE),
    ("pProperties", POINTER(SPPHRASEPROPERTY)),
    ("pElements", POINTER(SPPHRASEELEMENT)),
    ("cReplacements", c_ulong),
    ("pReplacements", POINTER(SPPHRASEREPLACEMENT)),
    ("SREngineID", comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
    ("ulSREnginePrivateDataSize", c_ulong),
    ("pSREnginePrivateData", POINTER(c_ubyte)),
    ("pSML", WSTRING),
    ("pSemanticErrorInfo", POINTER(SPSEMANTICERRORINFO)),
    ("SemanticTagFormat", SPSEMANTICFORMAT),
]
assert sizeof(SPPHRASE) == 128, sizeof(SPPHRASE)
assert alignment(SPPHRASE) == 8, alignment(SPPHRASE)

# values for enumeration 'DISPID_SpeechPhoneConverter'
DISPID_SPCLangId = 1
DISPID_SPCPhoneToId = 2
DISPID_SPCIdToPhone = 3
DISPID_SpeechPhoneConverter = c_int  # enum

# values for enumeration 'SPLEXICONTYPE'
eLEXTYPE_USER = 1
eLEXTYPE_APP = 2
eLEXTYPE_VENDORLEXICON = 4
eLEXTYPE_LETTERTOSOUND = 8
eLEXTYPE_MORPHOLOGY = 16
eLEXTYPE_RESERVED4 = 32
eLEXTYPE_USER_SHORTCUT = 64
eLEXTYPE_RESERVED6 = 128
eLEXTYPE_RESERVED7 = 256
eLEXTYPE_RESERVED8 = 512
eLEXTYPE_RESERVED9 = 1024
eLEXTYPE_RESERVED10 = 2048
eLEXTYPE_PRIVATE1 = 4096
eLEXTYPE_PRIVATE2 = 8192
eLEXTYPE_PRIVATE3 = 16384
eLEXTYPE_PRIVATE4 = 32768
eLEXTYPE_PRIVATE5 = 65536
eLEXTYPE_PRIVATE6 = 131072
eLEXTYPE_PRIVATE7 = 262144
eLEXTYPE_PRIVATE8 = 524288
eLEXTYPE_PRIVATE9 = 1048576
eLEXTYPE_PRIVATE10 = 2097152
eLEXTYPE_PRIVATE11 = 4194304
eLEXTYPE_PRIVATE12 = 8388608
eLEXTYPE_PRIVATE13 = 16777216
eLEXTYPE_PRIVATE14 = 33554432
eLEXTYPE_PRIVATE15 = 67108864
eLEXTYPE_PRIVATE16 = 134217728
eLEXTYPE_PRIVATE17 = 268435456
eLEXTYPE_PRIVATE18 = 536870912
eLEXTYPE_PRIVATE19 = 1073741824
eLEXTYPE_PRIVATE20 = -2147483648
SPLEXICONTYPE = c_int  # enum

# values for enumeration 'SPPARTOFSPEECH'
SPPS_NotOverriden = -1
SPPS_Unknown = 0
SPPS_Noun = 4096
SPPS_Verb = 8192
SPPS_Modifier = 12288
SPPS_Function = 16384
SPPS_Interjection = 20480
SPPS_Noncontent = 24576
SPPS_LMA = 28672
SPPS_SuppressWord = 61440
SPPARTOFSPEECH = c_int  # enum
SPWORDPRONUNCIATION._fields_ = [
    ("pNextWordPronunciation", POINTER(SPWORDPRONUNCIATION)),
    ("eLexiconType", SPLEXICONTYPE),
    ("LangId", c_ushort),
    ("wPronunciationFlags", c_ushort),
    ("ePartOfSpeech", SPPARTOFSPEECH),
    ("szPronunciation", c_ushort * 1),
]
assert sizeof(SPWORDPRONUNCIATION) == 20, sizeof(SPWORDPRONUNCIATION)
assert alignment(SPWORDPRONUNCIATION) == 4, alignment(SPWORDPRONUNCIATION)

# values for enumeration 'DISPID_SpeechLexiconPronunciation'
DISPID_SLPType = 1
DISPID_SLPLangId = 2
DISPID_SLPPartOfSpeech = 3
DISPID_SLPPhoneIds = 4
DISPID_SLPSymbolic = 5
DISPID_SpeechLexiconPronunciation = c_int  # enum


class ISpeechRecoGrammar(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechRecoGrammar Interface"
    _iid_ = GUID("{B6D6F79F-2158-4E50-B5BC-9A9CCD852A09}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechGrammarState'
SGSEnabled = 1
SGSDisabled = 0
SGSExclusive = 3
SpeechGrammarState = c_int  # enum


class ISpeechGrammarRules(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechGrammarRules Interface"
    _iid_ = GUID("{6FFA3B44-FC2D-40D1-8AFC-32911C7F1AD1}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechRecoGrammar._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Id"), "propget"],
        HRESULT,
        "Id",
        (["out", "retval"], POINTER(VARIANT), "Id"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("RecoContext"), "propget"],
        HRESULT,
        "RecoContext",
        (["out", "retval"], POINTER(POINTER(ISpeechRecoContext)), "RecoContext"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("State"), "propput"],
        HRESULT,
        "State",
        (["in"], SpeechGrammarState, "State"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("State"), "propget"],
        HRESULT,
        "State",
        (["out", "retval"], POINTER(SpeechGrammarState), "State"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Rules"), "propget"],
        HRESULT,
        "Rules",
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRules)), "Rules"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("Reset")],
        HRESULT,
        "Reset",
        (["in", "optional"], c_int, "NewLanguage", 0),
    ),
    COMMETHOD(
        [dispid(7), helpstring("CmdLoadFromFile")],
        HRESULT,
        "CmdLoadFromFile",
        (["in"], BSTR, "FileName"),
        (["in", "optional"], SpeechLoadOption, "LoadOption", 0),
    ),
    COMMETHOD(
        [dispid(8), helpstring("CmdLoadFromObject")],
        HRESULT,
        "CmdLoadFromObject",
        (["in"], BSTR, "ClassId"),
        (["in"], BSTR, "GrammarName"),
        (["in", "optional"], SpeechLoadOption, "LoadOption", 0),
    ),
    COMMETHOD(
        [dispid(9), helpstring("CmdLoadFromResource")],
        HRESULT,
        "CmdLoadFromResource",
        (["in"], c_int, "hModule"),
        (["in"], VARIANT, "ResourceName"),
        (["in"], VARIANT, "ResourceType"),
        (["in"], c_int, "LanguageId"),
        (["in", "optional"], SpeechLoadOption, "LoadOption", 0),
    ),
    COMMETHOD(
        [dispid(10), helpstring("CmdLoadFromMemory")],
        HRESULT,
        "CmdLoadFromMemory",
        (["in"], VARIANT, "GrammarData"),
        (["in", "optional"], SpeechLoadOption, "LoadOption", 0),
    ),
    COMMETHOD(
        [dispid(11), helpstring("CmdLoadFromProprietaryGrammar")],
        HRESULT,
        "CmdLoadFromProprietaryGrammar",
        (["in"], BSTR, "ProprietaryGuid"),
        (["in"], BSTR, "ProprietaryString"),
        (["in"], VARIANT, "ProprietaryData"),
        (["in", "optional"], SpeechLoadOption, "LoadOption", 0),
    ),
    COMMETHOD(
        [dispid(12), helpstring("CmdSetRuleState")],
        HRESULT,
        "CmdSetRuleState",
        (["in"], BSTR, "Name"),
        (["in"], SpeechRuleState, "State"),
    ),
    COMMETHOD(
        [dispid(13), helpstring("CmdSetRuleIdState")],
        HRESULT,
        "CmdSetRuleIdState",
        (["in"], c_int, "RuleId"),
        (["in"], SpeechRuleState, "State"),
    ),
    COMMETHOD(
        [dispid(14), helpstring("DictationLoad")],
        HRESULT,
        "DictationLoad",
        (["in", "optional"], BSTR, "TopicName", ""),
        (["in", "optional"], SpeechLoadOption, "LoadOption", 0),
    ),
    COMMETHOD([dispid(15), helpstring("DictationUnload")], HRESULT, "DictationUnload"),
    COMMETHOD(
        [dispid(16), helpstring("DictationSetState")],
        HRESULT,
        "DictationSetState",
        (["in"], SpeechRuleState, "State"),
    ),
    COMMETHOD(
        [dispid(17), helpstring("SetWordSequenceData")],
        HRESULT,
        "SetWordSequenceData",
        (["in"], BSTR, "Text"),
        (["in"], c_int, "TextLength"),
        (["in"], POINTER(ISpeechTextSelectionInformation), "Info"),
    ),
    COMMETHOD(
        [dispid(18), helpstring("SetTextSelection")],
        HRESULT,
        "SetTextSelection",
        (["in"], POINTER(ISpeechTextSelectionInformation), "Info"),
    ),
    COMMETHOD(
        [dispid(19), helpstring("IsPronounceable")],
        HRESULT,
        "IsPronounceable",
        (["in"], BSTR, "Word"),
        (["out", "retval"], POINTER(SpeechWordPronounceable), "WordPronounceable"),
    ),
]
################################################################
## code template for ISpeechRecoGrammar implementation
##class ISpeechRecoGrammar_Impl(object):
##    @property
##    def Id(self):
##        'Id'
##        #return Id
##
##    @property
##    def RecoContext(self):
##        'RecoContext'
##        #return RecoContext
##
##    def _get(self):
##        'State'
##        #return State
##    def _set(self, State):
##        'State'
##    State = property(_get, _set, doc = _set.__doc__)
##
##    @property
##    def Rules(self):
##        'Rules'
##        #return Rules
##
##    def Reset(self, NewLanguage):
##        'Reset'
##        #return
##
##    def CmdLoadFromFile(self, FileName, LoadOption):
##        'CmdLoadFromFile'
##        #return
##
##    def CmdLoadFromObject(self, ClassId, GrammarName, LoadOption):
##        'CmdLoadFromObject'
##        #return
##
##    def CmdLoadFromResource(self, hModule, ResourceName, ResourceType, LanguageId, LoadOption):
##        'CmdLoadFromResource'
##        #return
##
##    def CmdLoadFromMemory(self, GrammarData, LoadOption):
##        'CmdLoadFromMemory'
##        #return
##
##    def CmdLoadFromProprietaryGrammar(self, ProprietaryGuid, ProprietaryString, ProprietaryData, LoadOption):
##        'CmdLoadFromProprietaryGrammar'
##        #return
##
##    def CmdSetRuleState(self, Name, State):
##        'CmdSetRuleState'
##        #return
##
##    def CmdSetRuleIdState(self, RuleId, State):
##        'CmdSetRuleIdState'
##        #return
##
##    def DictationLoad(self, TopicName, LoadOption):
##        'DictationLoad'
##        #return
##
##    def DictationUnload(self):
##        'DictationUnload'
##        #return
##
##    def DictationSetState(self, State):
##        'DictationSetState'
##        #return
##
##    def SetWordSequenceData(self, Text, TextLength, Info):
##        'SetWordSequenceData'
##        #return
##
##    def SetTextSelection(self, Info):
##        'SetTextSelection'
##        #return
##
##    def IsPronounceable(self, Word):
##        'IsPronounceable'
##        #return WordPronounceable
##


class SpShortcut(CoClass):
    "SpShortcut Class"
    _reg_clsid_ = GUID("{0D722F1A-9FCF-4E62-96D8-6DF8F01A26AA}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpShortcut(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpShortcut Interface"
    _iid_ = GUID("{3DF681E2-EA56-11D9-8BDE-F66BAD1E3F3A}")
    _idlflags_ = ["restricted"]


SpShortcut._com_interfaces_ = [ISpShortcut, ISpObjectWithToken]


# values for enumeration 'SpeechBookmarkOptions'
SBONone = 0
SBOPause = 1
SpeechBookmarkOptions = c_int  # enum

# values for enumeration 'SpeechFormatType'
SFTInput = 0
SFTSREngine = 1
SpeechFormatType = c_int  # enum


class __MIDL___MIDL_itf_sapi_0000_0020_0001(Union):
    pass


class __MIDL___MIDL_itf_sapi_0000_0020_0002(Structure):
    pass


__MIDL___MIDL_itf_sapi_0000_0020_0002._fields_ = [
    ("bType", c_ubyte),
    ("bReserved", c_ubyte),
    ("usArrayIndex", c_ushort),
]
assert sizeof(__MIDL___MIDL_itf_sapi_0000_0020_0002) == 4, sizeof(
    __MIDL___MIDL_itf_sapi_0000_0020_0002
)
assert alignment(__MIDL___MIDL_itf_sapi_0000_0020_0002) == 2, alignment(
    __MIDL___MIDL_itf_sapi_0000_0020_0002
)
__MIDL___MIDL_itf_sapi_0000_0020_0001._fields_ = [
    ("ulId", c_ulong),
    ("__MIDL____MIDL_itf_sapi_0000_00200000", __MIDL___MIDL_itf_sapi_0000_0020_0002),
]
assert sizeof(__MIDL___MIDL_itf_sapi_0000_0020_0001) == 4, sizeof(
    __MIDL___MIDL_itf_sapi_0000_0020_0001
)
assert alignment(__MIDL___MIDL_itf_sapi_0000_0020_0001) == 4, alignment(
    __MIDL___MIDL_itf_sapi_0000_0020_0001
)
SPPHRASEPROPERTY._fields_ = [
    ("pszName", WSTRING),
    ("__MIDL____MIDL_itf_sapi_0000_00200001", __MIDL___MIDL_itf_sapi_0000_0020_0001),
    ("pszValue", WSTRING),
    ("vValue", VARIANT),
    ("ulFirstElement", c_ulong),
    ("ulCountOfElements", c_ulong),
    ("pNextSibling", POINTER(SPPHRASEPROPERTY)),
    ("pFirstChild", POINTER(SPPHRASEPROPERTY)),
    ("SREngineConfidence", c_float),
    ("Confidence", c_char),
]
assert sizeof(SPPHRASEPROPERTY) == 56, sizeof(SPPHRASEPROPERTY)
assert alignment(SPPHRASEPROPERTY) == 8, alignment(SPPHRASEPROPERTY)


class SpObjectTokenCategory(CoClass):
    "SpObjectTokenCategory Class"
    _reg_clsid_ = GUID("{A910187F-0C7A-45AC-92CC-59EDAFB77B53}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpeechObjectTokenCategory(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechObjectTokenCategory Interface"
    _iid_ = GUID("{CA7EAC50-2D01-4145-86D4-5AE7D70F4469}")
    _idlflags_ = ["dual", "oleautomation"]


SpObjectTokenCategory._com_interfaces_ = [
    ISpeechObjectTokenCategory,
    ISpObjectTokenCategory,
]

SPPHRASEELEMENT._fields_ = [
    ("ulAudioTimeOffset", c_ulong),
    ("ulAudioSizeTime", c_ulong),
    ("ulAudioStreamOffset", c_ulong),
    ("ulAudioSizeBytes", c_ulong),
    ("ulRetainedStreamOffset", c_ulong),
    ("ulRetainedSizeBytes", c_ulong),
    ("pszDisplayText", WSTRING),
    ("pszLexicalForm", WSTRING),
    ("pszPronunciation", POINTER(c_ushort)),
    ("bDisplayAttributes", c_ubyte),
    ("RequiredConfidence", c_char),
    ("ActualConfidence", c_char),
    ("reserved", c_ubyte),
    ("SREngineConfidence", c_float),
]
assert sizeof(SPPHRASEELEMENT) == 44, sizeof(SPPHRASEELEMENT)
assert alignment(SPPHRASEELEMENT) == 4, alignment(SPPHRASEELEMENT)


class ISpeechGrammarRule(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechGrammarRule Interface"
    _iid_ = GUID("{AFE719CF-5DD1-44F2-999C-7A399F1CFCCC}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechRuleAttributes'
SRATopLevel = 1
SRADefaultToActive = 2
SRAExport = 4
SRAImport = 8
SRAInterpreter = 16
SRADynamic = 32
SRARoot = 64
SpeechRuleAttributes = c_int  # enum
ISpeechGrammarRules._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("FindRule")],
        HRESULT,
        "FindRule",
        (["in"], VARIANT, "RuleNameOrId"),
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRule)), "Rule"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRule)), "Rule"),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the alternates"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Dynamic"), "propget"],
        HRESULT,
        "Dynamic",
        (["out", "retval"], POINTER(VARIANT_BOOL), "Dynamic"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Add")],
        HRESULT,
        "Add",
        (["in"], BSTR, "RuleName"),
        (["in"], SpeechRuleAttributes, "Attributes"),
        (["in", "optional"], c_int, "RuleId", 0),
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRule)), "Rule"),
    ),
    COMMETHOD([dispid(4), helpstring("Commit")], HRESULT, "Commit"),
    COMMETHOD(
        [dispid(5), helpstring("CommitAndSave")],
        HRESULT,
        "CommitAndSave",
        (["out"], POINTER(BSTR), "ErrorText"),
        (["out", "retval"], POINTER(VARIANT), "SaveStream"),
    ),
]
################################################################
## code template for ISpeechGrammarRules implementation
##class ISpeechGrammarRules_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def FindRule(self, RuleNameOrId):
##        'FindRule'
##        #return Rule
##
##    def Item(self, Index):
##        'Item'
##        #return Rule
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the alternates'
##        #return EnumVARIANT
##
##    @property
##    def Dynamic(self):
##        'Dynamic'
##        #return Dynamic
##
##    def Add(self, RuleName, Attributes, RuleId):
##        'Add'
##        #return Rule
##
##    def Commit(self):
##        'Commit'
##        #return
##
##    def CommitAndSave(self):
##        'CommitAndSave'
##        #return ErrorText, SaveStream
##


class ISpeechGrammarRuleState(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechGrammarRuleState Interface"
    _iid_ = GUID("{D4286F2C-EE67-45AE-B928-28D695362EDA}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechGrammarRule._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("RuleAttributes"), "propget"],
        HRESULT,
        "Attributes",
        (["out", "retval"], POINTER(SpeechRuleAttributes), "Attributes"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("InitialState"), "propget"],
        HRESULT,
        "InitialState",
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRuleState)), "State"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Name"), "propget"],
        HRESULT,
        "Name",
        (["out", "retval"], POINTER(BSTR), "Name"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Id"), "propget"],
        HRESULT,
        "Id",
        (["out", "retval"], POINTER(c_int), "Id"),
    ),
    COMMETHOD([dispid(5), helpstring("Clear")], HRESULT, "Clear"),
    COMMETHOD(
        [dispid(6), helpstring("AddResource")],
        HRESULT,
        "AddResource",
        (["in"], BSTR, "ResourceName"),
        (["in"], BSTR, "ResourceValue"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("AddState")],
        HRESULT,
        "AddState",
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRuleState)), "State"),
    ),
]
################################################################
## code template for ISpeechGrammarRule implementation
##class ISpeechGrammarRule_Impl(object):
##    @property
##    def Attributes(self):
##        'RuleAttributes'
##        #return Attributes
##
##    @property
##    def InitialState(self):
##        'InitialState'
##        #return State
##
##    @property
##    def Name(self):
##        'Name'
##        #return Name
##
##    @property
##    def Id(self):
##        'Id'
##        #return Id
##
##    def Clear(self):
##        'Clear'
##        #return
##
##    def AddResource(self, ResourceName, ResourceValue):
##        'AddResource'
##        #return
##
##    def AddState(self):
##        'AddState'
##        #return State
##


# values for enumeration 'SpeechRecognitionType'
SRTStandard = 0
SRTAutopause = 1
SRTEmulated = 2
SRTSMLTimeout = 4
SRTExtendableParse = 8
SRTReSent = 16
SpeechRecognitionType = c_int  # enum

# values for enumeration 'SpeechInterference'
SINone = 0
SINoise = 1
SINoSignal = 2
SITooLoud = 3
SITooQuiet = 4
SITooFast = 5
SITooSlow = 6
SpeechInterference = c_int  # enum

# values for enumeration 'SpeechRecognizerState'
SRSInactive = 0
SRSActive = 1
SRSActiveAlways = 2
SRSInactiveWithPurge = 3
SpeechRecognizerState = c_int  # enum
_ISpeechRecoContextEvents._disp_methods_ = [
    DISPMETHOD(
        [dispid(1), helpstring("StartStream")],
        None,
        "StartStream",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(2), helpstring("EndStream")],
        None,
        "EndStream",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], VARIANT_BOOL, "StreamReleased"),
    ),
    DISPMETHOD(
        [dispid(3), helpstring("Bookmark")],
        None,
        "Bookmark",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], VARIANT, "BookmarkId"),
        (["in"], SpeechBookmarkOptions, "Options"),
    ),
    DISPMETHOD(
        [dispid(4), helpstring("SoundStart")],
        None,
        "SoundStart",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(5), helpstring("SoundEnd")],
        None,
        "SoundEnd",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(6), helpstring("PhraseStart")],
        None,
        "PhraseStart",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(7), helpstring("Recognition")],
        None,
        "Recognition",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], SpeechRecognitionType, "RecognitionType"),
        (["in"], POINTER(ISpeechRecoResult), "Result"),
    ),
    DISPMETHOD(
        [dispid(8), helpstring("Hypothesis")],
        None,
        "Hypothesis",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], POINTER(ISpeechRecoResult), "Result"),
    ),
    DISPMETHOD(
        [dispid(9), helpstring("PropertyNumberChange")],
        None,
        "PropertyNumberChange",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], BSTR, "PropertyName"),
        (["in"], c_int, "NewNumberValue"),
    ),
    DISPMETHOD(
        [dispid(10), helpstring("PropertyStringChange")],
        None,
        "PropertyStringChange",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], BSTR, "PropertyName"),
        (["in"], BSTR, "NewStringValue"),
    ),
    DISPMETHOD(
        [dispid(11), helpstring("FalseRecognition")],
        None,
        "FalseRecognition",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], POINTER(ISpeechRecoResult), "Result"),
    ),
    DISPMETHOD(
        [dispid(12), helpstring("Interference")],
        None,
        "Interference",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], SpeechInterference, "Interference"),
    ),
    DISPMETHOD(
        [dispid(13), helpstring("RequestUI")],
        None,
        "RequestUI",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], BSTR, "UIType"),
    ),
    DISPMETHOD(
        [dispid(14), helpstring("RecognizerStateChange")],
        None,
        "RecognizerStateChange",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], SpeechRecognizerState, "NewState"),
    ),
    DISPMETHOD(
        [dispid(15), helpstring("Adaptation")],
        None,
        "Adaptation",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(16), helpstring("RecognitionForOtherContext")],
        None,
        "RecognitionForOtherContext",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(17), helpstring("AudioLevel")],
        None,
        "AudioLevel",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], c_int, "AudioLevel"),
    ),
    DISPMETHOD(
        [dispid(18), helpstring("EnginePrivate")],
        None,
        "EnginePrivate",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], VARIANT, "EngineData"),
    ),
]


class _RemotableHandle(Structure):
    pass


class __MIDL_IWinTypes_0009(Union):
    pass


__MIDL_IWinTypes_0009._fields_ = [
    ("hInproc", c_int),
    ("hRemote", c_int),
]
assert sizeof(__MIDL_IWinTypes_0009) == 4, sizeof(__MIDL_IWinTypes_0009)
assert alignment(__MIDL_IWinTypes_0009) == 4, alignment(__MIDL_IWinTypes_0009)
_RemotableHandle._fields_ = [
    ("fContext", c_int),
    ("u", __MIDL_IWinTypes_0009),
]
assert sizeof(_RemotableHandle) == 8, sizeof(_RemotableHandle)
assert alignment(_RemotableHandle) == 4, alignment(_RemotableHandle)

# values for enumeration 'SPSHORTCUTTYPE'
SPSHT_NotOverriden = -1
SPSHT_Unknown = 0
SPSHT_EMAIL = 4096
SPSHT_OTHER = 8192
SPPS_RESERVED1 = 12288
SPPS_RESERVED2 = 16384
SPPS_RESERVED3 = 20480
SPPS_RESERVED4 = 61440
SPSHORTCUTTYPE = c_int  # enum


class SPSHORTCUTPAIRLIST(Structure):
    pass


class SPWORDLIST(Structure):
    pass


ISpShortcut._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "AddShortcut",
        (["in"], WSTRING, "pszDisplay"),
        (["in"], c_ushort, "LangId"),
        (["in"], WSTRING, "pszSpoken"),
        (["in"], SPSHORTCUTTYPE, "shType"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "RemoveShortcut",
        (["in"], WSTRING, "pszDisplay"),
        (["in"], c_ushort, "LangId"),
        (["in"], WSTRING, "pszSpoken"),
        (["in"], SPSHORTCUTTYPE, "shType"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetShortcuts",
        (["in"], c_ushort, "LangId"),
        (["in", "out"], POINTER(SPSHORTCUTPAIRLIST), "pShortcutpairList"),
    ),
    COMMETHOD(
        [], HRESULT, "GetGeneration", (["out"], POINTER(c_ulong), "pdwGeneration")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetWordsFromGenerationChange",
        (["in", "out"], POINTER(c_ulong), "pdwGeneration"),
        (["in", "out"], POINTER(SPWORDLIST), "pWordList"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetWords",
        (["in", "out"], POINTER(c_ulong), "pdwGeneration"),
        (["in", "out"], POINTER(c_ulong), "pdwCookie"),
        (["in", "out"], POINTER(SPWORDLIST), "pWordList"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetShortcutsForGeneration",
        (["in", "out"], POINTER(c_ulong), "pdwGeneration"),
        (["in", "out"], POINTER(c_ulong), "pdwCookie"),
        (["in", "out"], POINTER(SPSHORTCUTPAIRLIST), "pShortcutpairList"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetGenerationChange",
        (["in", "out"], POINTER(c_ulong), "pdwGeneration"),
        (["in", "out"], POINTER(SPSHORTCUTPAIRLIST), "pShortcutpairList"),
    ),
]
################################################################
## code template for ISpShortcut implementation
##class ISpShortcut_Impl(object):
##    def AddShortcut(self, pszDisplay, LangId, pszSpoken, shType):
##        '-no docstring-'
##        #return
##
##    def RemoveShortcut(self, pszDisplay, LangId, pszSpoken, shType):
##        '-no docstring-'
##        #return
##
##    def GetShortcuts(self, LangId):
##        '-no docstring-'
##        #return pShortcutpairList
##
##    def GetGeneration(self):
##        '-no docstring-'
##        #return pdwGeneration
##
##    def GetWordsFromGenerationChange(self):
##        '-no docstring-'
##        #return pdwGeneration, pWordList
##
##    def GetWords(self):
##        '-no docstring-'
##        #return pdwGeneration, pdwCookie, pWordList
##
##    def GetShortcutsForGeneration(self):
##        '-no docstring-'
##        #return pdwGeneration, pdwCookie, pShortcutpairList
##
##    def GetGenerationChange(self):
##        '-no docstring-'
##        #return pdwGeneration, pShortcutpairList
##


class SPWORD(Structure):
    pass


SPWORDLIST._fields_ = [
    ("ulSize", c_ulong),
    ("pvBuffer", POINTER(c_ubyte)),
    ("pFirstWord", POINTER(SPWORD)),
]
assert sizeof(SPWORDLIST) == 12, sizeof(SPWORDLIST)
assert alignment(SPWORDLIST) == 4, alignment(SPWORDLIST)


class SpUnCompressedLexicon(CoClass):
    "SpUnCompressedLexicon Class"
    _reg_clsid_ = GUID("{C9E37C15-DF92-4727-85D6-72E5EEB6995A}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpeechLexicon(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechLexicon Interface"
    _iid_ = GUID("{3DA7627A-C7AE-4B23-8708-638C50362C25}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpLexicon(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpLexicon Interface"
    _iid_ = GUID("{DA41A7C2-5383-4DB2-916B-6C1719E3DB58}")
    _idlflags_ = ["restricted"]


SpUnCompressedLexicon._com_interfaces_ = [
    ISpeechLexicon,
    ISpLexicon,
    ISpObjectWithToken,
    ISpPhoneticAlphabetSelection,
]

SPPHRASEREPLACEMENT._fields_ = [
    ("bDisplayAttributes", c_ubyte),
    ("pszReplacementText", WSTRING),
    ("ulFirstElement", c_ulong),
    ("ulCountOfElements", c_ulong),
]
assert sizeof(SPPHRASEREPLACEMENT) == 16, sizeof(SPPHRASEREPLACEMENT)
assert alignment(SPPHRASEREPLACEMENT) == 4, alignment(SPPHRASEREPLACEMENT)


class ISpeechGrammarRuleStateTransitions(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechGrammarRuleStateTransitions Interface"
    _iid_ = GUID("{EABCE657-75BC-44A2-AA7F-C56476742963}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechGrammarWordType'
SGDisplay = 0
SGLexical = 1
SGPronounciation = 2
SGLexicalNoSpecialChars = 3
SpeechGrammarWordType = c_int  # enum

# values for enumeration 'SpeechSpecialTransitionType'
SSTTWildcard = 1
SSTTDictation = 2
SSTTTextBuffer = 3
SpeechSpecialTransitionType = c_int  # enum
ISpeechGrammarRuleState._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Rule"), "propget"],
        HRESULT,
        "Rule",
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRule)), "Rule"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Transitions"), "propget"],
        HRESULT,
        "Transitions",
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechGrammarRuleStateTransitions)),
            "Transitions",
        ),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AddWordTransition")],
        HRESULT,
        "AddWordTransition",
        (["in"], POINTER(ISpeechGrammarRuleState), "DestState"),
        (["in"], BSTR, "Words"),
        (["in", "optional"], BSTR, "Separators", " "),
        (["in", "optional"], SpeechGrammarWordType, "Type", 1),
        (["in", "optional"], BSTR, "PropertyName", ""),
        (["in", "optional"], c_int, "PropertyId", 0),
        (["in", "optional"], POINTER(VARIANT), "PropertyValue"),
        (["in", "optional"], c_float, "Weight", 1.0),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AddRuleTransition")],
        HRESULT,
        "AddRuleTransition",
        (["in"], POINTER(ISpeechGrammarRuleState), "DestinationState"),
        (["in"], POINTER(ISpeechGrammarRule), "Rule"),
        (["in", "optional"], BSTR, "PropertyName", ""),
        (["in", "optional"], c_int, "PropertyId", 0),
        (["in", "optional"], POINTER(VARIANT), "PropertyValue"),
        (["in", "optional"], c_float, "Weight", 1.0),
    ),
    COMMETHOD(
        [dispid(5), helpstring("AddSpecialTransition")],
        HRESULT,
        "AddSpecialTransition",
        (["in"], POINTER(ISpeechGrammarRuleState), "DestinationState"),
        (["in"], SpeechSpecialTransitionType, "Type"),
        (["in", "optional"], BSTR, "PropertyName", ""),
        (["in", "optional"], c_int, "PropertyId", 0),
        (["in", "optional"], POINTER(VARIANT), "PropertyValue"),
        (["in", "optional"], c_float, "Weight", 1.0),
    ),
]
################################################################
## code template for ISpeechGrammarRuleState implementation
##class ISpeechGrammarRuleState_Impl(object):
##    @property
##    def Rule(self):
##        'Rule'
##        #return Rule
##
##    @property
##    def Transitions(self):
##        'Transitions'
##        #return Transitions
##
##    def AddWordTransition(self, DestState, Words, Separators, Type, PropertyName, PropertyId, PropertyValue, Weight):
##        'AddWordTransition'
##        #return
##
##    def AddRuleTransition(self, DestinationState, Rule, PropertyName, PropertyId, PropertyValue, Weight):
##        'AddRuleTransition'
##        #return
##
##    def AddSpecialTransition(self, DestinationState, Type, PropertyName, PropertyId, PropertyValue, Weight):
##        'AddSpecialTransition'
##        #return
##

ISpObjectTokenCategory._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetId",
        (["in"], WSTRING, "pszCategoryId"),
        (["in"], c_int, "fCreateIfNotExist"),
    ),
    COMMETHOD([], HRESULT, "GetId", (["out"], POINTER(WSTRING), "ppszCoMemCategoryId")),
    COMMETHOD(
        [],
        HRESULT,
        "GetDataKey",
        (["in"], SPDATAKEYLOCATION, "spdkl"),
        (["out"], POINTER(POINTER(ISpDataKey)), "ppDataKey"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "EnumTokens",
        (["in"], WSTRING, "pzsReqAttribs"),
        (["in"], WSTRING, "pszOptAttribs"),
        (["out"], POINTER(POINTER(IEnumSpObjectTokens)), "ppEnum"),
    ),
    COMMETHOD([], HRESULT, "SetDefaultTokenId", (["in"], WSTRING, "pszTokenId")),
    COMMETHOD(
        [],
        HRESULT,
        "GetDefaultTokenId",
        (["out"], POINTER(WSTRING), "ppszCoMemTokenId"),
    ),
]
################################################################
## code template for ISpObjectTokenCategory implementation
##class ISpObjectTokenCategory_Impl(object):
##    def SetId(self, pszCategoryId, fCreateIfNotExist):
##        '-no docstring-'
##        #return
##
##    def GetId(self):
##        '-no docstring-'
##        #return ppszCoMemCategoryId
##
##    def GetDataKey(self, spdkl):
##        '-no docstring-'
##        #return ppDataKey
##
##    def EnumTokens(self, pzsReqAttribs, pszOptAttribs):
##        '-no docstring-'
##        #return ppEnum
##
##    def SetDefaultTokenId(self, pszTokenId):
##        '-no docstring-'
##        #return
##
##    def GetDefaultTokenId(self):
##        '-no docstring-'
##        #return ppszCoMemTokenId
##


# values for enumeration 'SpeechLexiconType'
SLTUser = 1
SLTApp = 2
SpeechLexiconType = c_int  # enum


class ISpeechLexiconWords(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechLexiconWords Interface"
    _iid_ = GUID("{8D199862-415E-47D5-AC4F-FAA608B424E6}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechPartOfSpeech'
SPSNotOverriden = -1
SPSUnknown = 0
SPSNoun = 4096
SPSVerb = 8192
SPSModifier = 12288
SPSFunction = 16384
SPSInterjection = 20480
SPSLMA = 28672
SPSSuppressWord = 61440
SpeechPartOfSpeech = c_int  # enum


class ISpeechLexiconPronunciations(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechLexiconPronunciations Interface"
    _iid_ = GUID("{72829128-5682-4704-A0D4-3E2BB6F2EAD3}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechLexicon._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("GenerationId"), "hidden", "propget"],
        HRESULT,
        "GenerationId",
        (["out", "retval"], POINTER(c_int), "GenerationId"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("GetWords")],
        HRESULT,
        "GetWords",
        (["in", "optional"], SpeechLexiconType, "Flags", 3),
        (["out", "optional"], POINTER(c_int), "GenerationId", 0),
        (["out", "retval"], POINTER(POINTER(ISpeechLexiconWords)), "Words"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AddPronunciation")],
        HRESULT,
        "AddPronunciation",
        (["in"], BSTR, "bstrWord"),
        (["in"], c_int, "LangId"),
        (["in", "optional"], SpeechPartOfSpeech, "PartOfSpeech", 0),
        (["in", "optional"], BSTR, "bstrPronunciation", ""),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AddPronunciationByPhoneIds"), "hidden"],
        HRESULT,
        "AddPronunciationByPhoneIds",
        (["in"], BSTR, "bstrWord"),
        (["in"], c_int, "LangId"),
        (["in", "optional"], SpeechPartOfSpeech, "PartOfSpeech", 0),
        (["in", "optional"], POINTER(VARIANT), "PhoneIds"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("RemovePronunciation")],
        HRESULT,
        "RemovePronunciation",
        (["in"], BSTR, "bstrWord"),
        (["in"], c_int, "LangId"),
        (["in", "optional"], SpeechPartOfSpeech, "PartOfSpeech", 0),
        (["in", "optional"], BSTR, "bstrPronunciation", ""),
    ),
    COMMETHOD(
        [dispid(6), helpstring("RemovePronunciationByPhoneIds"), "hidden"],
        HRESULT,
        "RemovePronunciationByPhoneIds",
        (["in"], BSTR, "bstrWord"),
        (["in"], c_int, "LangId"),
        (["in", "optional"], SpeechPartOfSpeech, "PartOfSpeech", 0),
        (["in", "optional"], POINTER(VARIANT), "PhoneIds"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("GetPronunciations")],
        HRESULT,
        "GetPronunciations",
        (["in"], BSTR, "bstrWord"),
        (["in", "optional"], c_int, "LangId", 0),
        (["in", "optional"], SpeechLexiconType, "TypeFlags", 3),
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechLexiconPronunciations)),
            "ppPronunciations",
        ),
    ),
    COMMETHOD(
        [dispid(8), helpstring("GetGenerationChange"), "hidden"],
        HRESULT,
        "GetGenerationChange",
        (["in", "out"], POINTER(c_int), "GenerationId"),
        (["out", "retval"], POINTER(POINTER(ISpeechLexiconWords)), "ppWords"),
    ),
]
################################################################
## code template for ISpeechLexicon implementation
##class ISpeechLexicon_Impl(object):
##    @property
##    def GenerationId(self):
##        'GenerationId'
##        #return GenerationId
##
##    def GetWords(self, Flags):
##        'GetWords'
##        #return GenerationId, Words
##
##    def AddPronunciation(self, bstrWord, LangId, PartOfSpeech, bstrPronunciation):
##        'AddPronunciation'
##        #return
##
##    def AddPronunciationByPhoneIds(self, bstrWord, LangId, PartOfSpeech, PhoneIds):
##        'AddPronunciationByPhoneIds'
##        #return
##
##    def RemovePronunciation(self, bstrWord, LangId, PartOfSpeech, bstrPronunciation):
##        'RemovePronunciation'
##        #return
##
##    def RemovePronunciationByPhoneIds(self, bstrWord, LangId, PartOfSpeech, PhoneIds):
##        'RemovePronunciationByPhoneIds'
##        #return
##
##    def GetPronunciations(self, bstrWord, LangId, TypeFlags):
##        'GetPronunciations'
##        #return ppPronunciations
##
##    def GetGenerationChange(self):
##        'GetGenerationChange'
##        #return GenerationId, ppWords
##


# values for enumeration 'SPWORDTYPE'
eWORDTYPE_ADDED = 1
eWORDTYPE_DELETED = 2
SPWORDTYPE = c_int  # enum
SPWORD._fields_ = [
    ("pNextWord", POINTER(SPWORD)),
    ("LangId", c_ushort),
    ("wReserved", c_ushort),
    ("eWordType", SPWORDTYPE),
    ("pszWord", WSTRING),
    ("pFirstWordPronunciation", POINTER(SPWORDPRONUNCIATION)),
]
assert sizeof(SPWORD) == 20, sizeof(SPWORD)
assert alignment(SPWORD) == 4, alignment(SPWORD)


class SpCompressedLexicon(CoClass):
    "SpCompressedLexicon Class"
    _reg_clsid_ = GUID("{90903716-2F42-11D3-9C26-00C04F8EF87C}")
    _idlflags_ = ["hidden", "restricted"]
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpCompressedLexicon._com_interfaces_ = [ISpLexicon, ISpObjectWithToken]

SPSEMANTICERRORINFO._fields_ = [
    ("ulLineNumber", c_ulong),
    ("pszScriptLine", WSTRING),
    ("pszSource", WSTRING),
    ("pszDescription", WSTRING),
    ("hrResultCode", HRESULT),
]
assert sizeof(SPSEMANTICERRORINFO) == 20, sizeof(SPSEMANTICERRORINFO)
assert alignment(SPSEMANTICERRORINFO) == 4, alignment(SPSEMANTICERRORINFO)


class ISpeechGrammarRuleStateTransition(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechGrammarRuleStateTransition Interface"
    _iid_ = GUID("{CAFD1DB1-41D1-4A06-9863-E2E81DA17A9A}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechGrammarRuleStateTransitions._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechGrammarRuleStateTransition)),
            "Transition",
        ),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the transitions"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechGrammarRuleStateTransitions implementation
##class ISpeechGrammarRuleStateTransitions_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Transition
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the transitions'
##        #return EnumVARIANT
##


class ISpeechRecoResultDispatch(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechRecoResultDispatch Interface"
    _iid_ = GUID("{6D60EB64-ACED-40A6-BBF3-4E557F71DEE2}")
    _idlflags_ = ["hidden", "dual", "oleautomation"]


ISpeechRecoResultDispatch._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("RecoContext"), "propget"],
        HRESULT,
        "RecoContext",
        (["out", "retval"], POINTER(POINTER(ISpeechRecoContext)), "RecoContext"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Times"), "propget"],
        HRESULT,
        "Times",
        (["out", "retval"], POINTER(POINTER(ISpeechRecoResultTimes)), "Times"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AudioFormat"), "propputref"],
        HRESULT,
        "AudioFormat",
        (["in"], POINTER(ISpeechAudioFormat), "Format"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AudioFormat"), "propget"],
        HRESULT,
        "AudioFormat",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioFormat)), "Format"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("PhraseInfo"), "propget"],
        HRESULT,
        "PhraseInfo",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseInfo)), "PhraseInfo"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("Alternates")],
        HRESULT,
        "Alternates",
        (["in"], c_int, "RequestCount"),
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseAlternates)), "Alternates"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("Audio")],
        HRESULT,
        "Audio",
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["out", "retval"], POINTER(POINTER(ISpeechMemoryStream)), "Stream"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("SpeakAudio")],
        HRESULT,
        "SpeakAudio",
        (["in", "optional"], c_int, "StartElement", 0),
        (["in", "optional"], c_int, "Elements", -1),
        (["in", "optional"], SpeechVoiceSpeakFlags, "Flags", 0),
        (["out", "retval"], POINTER(c_int), "StreamNumber"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("SaveToMemory")],
        HRESULT,
        "SaveToMemory",
        (["out", "retval"], POINTER(VARIANT), "ResultBlock"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("DiscardResultInfo")],
        HRESULT,
        "DiscardResultInfo",
        (["in"], SpeechDiscardType, "ValueTypes"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("GetXMLResult")],
        HRESULT,
        "GetXMLResult",
        (["in"], SPXMLRESULTOPTIONS, "Options"),
        (["out", "retval"], POINTER(BSTR), "pResult"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("GetXMLErrorInfo")],
        HRESULT,
        "GetXMLErrorInfo",
        (["out"], POINTER(c_int), "LineNumber"),
        (["out"], POINTER(BSTR), "ScriptLine"),
        (["out"], POINTER(BSTR), "Source"),
        (["out"], POINTER(BSTR), "Description"),
        (["out"], POINTER(HRESULT), "ResultCode"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "IsError"),
    ),
    COMMETHOD(
        [dispid(12), helpstring("SetTextFeedback")],
        HRESULT,
        "SetTextFeedback",
        (["in"], BSTR, "Feedback"),
        (["in"], VARIANT_BOOL, "WasSuccessful"),
    ),
]
################################################################
## code template for ISpeechRecoResultDispatch implementation
##class ISpeechRecoResultDispatch_Impl(object):
##    @property
##    def RecoContext(self):
##        'RecoContext'
##        #return RecoContext
##
##    @property
##    def Times(self):
##        'Times'
##        #return Times
##
##    @property
##    def AudioFormat(self, Format):
##        'AudioFormat'
##        #return
##
##    @property
##    def PhraseInfo(self):
##        'PhraseInfo'
##        #return PhraseInfo
##
##    def Alternates(self, RequestCount, StartElement, Elements):
##        'Alternates'
##        #return Alternates
##
##    def Audio(self, StartElement, Elements):
##        'Audio'
##        #return Stream
##
##    def SpeakAudio(self, StartElement, Elements, Flags):
##        'SpeakAudio'
##        #return StreamNumber
##
##    def SaveToMemory(self):
##        'SaveToMemory'
##        #return ResultBlock
##
##    def DiscardResultInfo(self, ValueTypes):
##        'DiscardResultInfo'
##        #return
##
##    def GetXMLResult(self, Options):
##        'GetXMLResult'
##        #return pResult
##
##    def GetXMLErrorInfo(self):
##        'GetXMLErrorInfo'
##        #return LineNumber, ScriptLine, Source, Description, ResultCode, IsError
##
##    def SetTextFeedback(self, Feedback, WasSuccessful):
##        'SetTextFeedback'
##        #return
##


# values for enumeration 'DISPID_SpeechWaveFormatEx'
DISPID_SWFEFormatTag = 1
DISPID_SWFEChannels = 2
DISPID_SWFESamplesPerSec = 3
DISPID_SWFEAvgBytesPerSec = 4
DISPID_SWFEBlockAlign = 5
DISPID_SWFEBitsPerSample = 6
DISPID_SWFEExtraData = 7
DISPID_SpeechWaveFormatEx = c_int  # enum
SpeechRegistryUserRoot = (
    "HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Speech"  # Constant BSTR
)


class ISpeechLexiconWord(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechLexiconWord Interface"
    _iid_ = GUID("{4E5B933C-C9BE-48ED-8842-1EE51BB1D4FF}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechLexiconWords._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(POINTER(ISpeechLexiconWord)), "Word"),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the tokens"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechLexiconWords implementation
##class ISpeechLexiconWords_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Word
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the tokens'
##        #return EnumVARIANT
##


# values for enumeration 'SpeechWordType'
SWTAdded = 1
SWTDeleted = 2
SpeechWordType = c_int  # enum
ISpeechLexiconWord._methods_ = [
    COMMETHOD(
        [dispid(1), "propget"],
        HRESULT,
        "LangId",
        (["out", "retval"], POINTER(c_int), "LangId"),
    ),
    COMMETHOD(
        [dispid(2), "propget"],
        HRESULT,
        "Type",
        (["out", "retval"], POINTER(SpeechWordType), "WordType"),
    ),
    COMMETHOD(
        [dispid(3), "propget"],
        HRESULT,
        "Word",
        (["out", "retval"], POINTER(BSTR), "Word"),
    ),
    COMMETHOD(
        [dispid(4), "propget"],
        HRESULT,
        "Pronunciations",
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechLexiconPronunciations)),
            "Pronunciations",
        ),
    ),
]
################################################################
## code template for ISpeechLexiconWord implementation
##class ISpeechLexiconWord_Impl(object):
##    @property
##    def LangId(self):
##        '-no docstring-'
##        #return LangId
##
##    @property
##    def Type(self):
##        '-no docstring-'
##        #return WordType
##
##    @property
##    def Word(self):
##        '-no docstring-'
##        #return Word
##
##    @property
##    def Pronunciations(self):
##        '-no docstring-'
##        #return Pronunciations
##


# values for enumeration 'SPADAPTATIONRELEVANCE'
SPAR_Unknown = 0
SPAR_Low = 1
SPAR_Medium = 2
SPAR_High = 3
SPADAPTATIONRELEVANCE = c_int  # enum
ISpRecoContext2._methods_ = [
    COMMETHOD([], HRESULT, "SetGrammarOptions", (["in"], c_ulong, "eGrammarOptions")),
    COMMETHOD(
        [],
        HRESULT,
        "GetGrammarOptions",
        (["out"], POINTER(c_ulong), "peGrammarOptions"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetAdaptationData2",
        (["in"], WSTRING, "pAdaptationData"),
        (["in"], c_ulong, "cch"),
        (["in"], WSTRING, "pTopicName"),
        (["in"], c_ulong, "eAdaptationSettings"),
        (["in"], SPADAPTATIONRELEVANCE, "eRelevance"),
    ),
]
################################################################
## code template for ISpRecoContext2 implementation
##class ISpRecoContext2_Impl(object):
##    def SetGrammarOptions(self, eGrammarOptions):
##        '-no docstring-'
##        #return
##
##    def GetGrammarOptions(self):
##        '-no docstring-'
##        #return peGrammarOptions
##
##    def SetAdaptationData2(self, pAdaptationData, cch, pTopicName, eAdaptationSettings, eRelevance):
##        '-no docstring-'
##        #return
##


# values for enumeration 'SPBOOKMARKOPTIONS'
SPBO_NONE = 0
SPBO_PAUSE = 1
SPBO_AHEAD = 2
SPBO_TIME_UNITS = 4
SPBOOKMARKOPTIONS = c_int  # enum

# values for enumeration 'SPCONTEXTSTATE'
SPCS_DISABLED = 0
SPCS_ENABLED = 1
SPCONTEXTSTATE = c_int  # enum


class SpInprocRecognizer(CoClass):
    "SpInprocRecognizer Class"
    _reg_clsid_ = GUID("{41B89B6B-9399-11D2-9623-00C04F8EE628}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpeechRecognizer(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechRecognizer Interface"
    _iid_ = GUID("{2D5F1C0C-BD75-4B08-9478-3B11FEA2586C}")
    _idlflags_ = ["dual", "oleautomation"]


class ISpRecognizer2(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpRecognizer2 Interface"
    _iid_ = GUID("{8FC6D974-C81E-4098-93C5-0147F61ED4D3}")
    _idlflags_ = ["restricted"]


class ISpRecognizer3(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    "ISpRecognizer3 Interface"
    _iid_ = GUID("{DF1B943C-5838-4AA2-8706-D7CD5B333499}")
    _idlflags_ = ["restricted"]


class ISpSerializeState(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpSerializeState Interface"
    _iid_ = GUID("{21B501A0-0EC7-46C9-92C3-A2BC784C54B9}")
    _idlflags_ = ["restricted"]


SpInprocRecognizer._com_interfaces_ = [
    ISpeechRecognizer,
    ISpRecognizer,
    ISpRecognizer2,
    ISpRecognizer3,
    ISpSerializeState,
]


class ISpRecoCategory(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpRecoCategory Interface"
    _iid_ = GUID("{DA0CD0F9-14A2-4F09-8C2A-85CC48979345}")
    _idlflags_ = ["restricted"]


# values for enumeration 'SPCATEGORYTYPE'
SPCT_COMMAND = 0
SPCT_DICTATION = 1
SPCT_SLEEP = 2
SPCT_SUB_COMMAND = 3
SPCT_SUB_DICTATION = 4
SPCATEGORYTYPE = c_int  # enum
ISpRecoCategory._methods_ = [
    COMMETHOD(
        [], HRESULT, "GetType", (["out"], POINTER(SPCATEGORYTYPE), "peCategoryType")
    ),
]
################################################################
## code template for ISpRecoCategory implementation
##class ISpRecoCategory_Impl(object):
##    def GetType(self):
##        '-no docstring-'
##        #return peCategoryType
##

ISpRecognizer3._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetCategory",
        (["in"], SPCATEGORYTYPE, "categoryType"),
        (["out"], POINTER(POINTER(ISpRecoCategory)), "ppCategory"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetActiveCategory",
        (["in"], POINTER(ISpRecoCategory), "pCategory"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetActiveCategory",
        (["out"], POINTER(POINTER(ISpRecoCategory)), "ppCategory"),
    ),
]
################################################################
## code template for ISpRecognizer3 implementation
##class ISpRecognizer3_Impl(object):
##    def GetCategory(self, categoryType):
##        '-no docstring-'
##        #return ppCategory
##
##    def SetActiveCategory(self, pCategory):
##        '-no docstring-'
##        #return
##
##    def GetActiveCategory(self):
##        '-no docstring-'
##        #return ppCategory
##

ISpRecognizer2._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "EmulateRecognitionEx",
        (["in"], POINTER(ISpPhrase), "pPhrase"),
        (["in"], c_ulong, "dwCompareFlags"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetTrainingState",
        (["in"], c_int, "fDoingTraining"),
        (["in"], c_int, "fAdaptFromTrainingData"),
    ),
    COMMETHOD([], HRESULT, "ResetAcousticModelAdaptation"),
]
################################################################
## code template for ISpRecognizer2 implementation
##class ISpRecognizer2_Impl(object):
##    def EmulateRecognitionEx(self, pPhrase, dwCompareFlags):
##        '-no docstring-'
##        #return
##
##    def SetTrainingState(self, fDoingTraining, fAdaptFromTrainingData):
##        '-no docstring-'
##        #return
##
##    def ResetAcousticModelAdaptation(self):
##        '-no docstring-'
##        #return
##


class ISpeechLexiconPronunciation(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechLexiconPronunciation Interface"
    _iid_ = GUID("{95252C5D-9E43-4F4A-9899-48EE73352F9F}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechLexiconPronunciations._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechLexiconPronunciation)),
            "Pronunciation",
        ),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the tokens"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "EnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechLexiconPronunciations implementation
##class ISpeechLexiconPronunciations_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Pronunciation
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the tokens'
##        #return EnumVARIANT
##

SpeechRegistryLocalMachineRoot = (
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech"  # Constant BSTR
)
ISpeechLexiconPronunciation._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Type"), "propget"],
        HRESULT,
        "Type",
        (["out", "retval"], POINTER(SpeechLexiconType), "LexiconType"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("LangId"), "propget"],
        HRESULT,
        "LangId",
        (["out", "retval"], POINTER(c_int), "LangId"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("PartOfSpeech"), "propget"],
        HRESULT,
        "PartOfSpeech",
        (["out", "retval"], POINTER(SpeechPartOfSpeech), "PartOfSpeech"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("PhoneIds"), "propget"],
        HRESULT,
        "PhoneIds",
        (["out", "retval"], POINTER(VARIANT), "PhoneIds"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("Symbolic"), "propget"],
        HRESULT,
        "Symbolic",
        (["out", "retval"], POINTER(BSTR), "Symbolic"),
    ),
]
################################################################
## code template for ISpeechLexiconPronunciation implementation
##class ISpeechLexiconPronunciation_Impl(object):
##    @property
##    def Type(self):
##        'Type'
##        #return LexiconType
##
##    @property
##    def LangId(self):
##        'LangId'
##        #return LangId
##
##    @property
##    def PartOfSpeech(self):
##        'PartOfSpeech'
##        #return PartOfSpeech
##
##    @property
##    def PhoneIds(self):
##        'PhoneIds'
##        #return PhoneIds
##
##    @property
##    def Symbolic(self):
##        'Symbolic'
##        #return Symbolic
##

ISpSerializeState._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetSerializedState",
        (["out"], POINTER(POINTER(c_ubyte)), "ppbData"),
        (["out"], POINTER(c_ulong), "pulSize"),
        (["in"], c_ulong, "dwReserved"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetSerializedState",
        (["in"], POINTER(c_ubyte), "pbData"),
        (["in"], c_ulong, "ulSize"),
        (["in"], c_ulong, "dwReserved"),
    ),
]
################################################################
## code template for ISpSerializeState implementation
##class ISpSerializeState_Impl(object):
##    def GetSerializedState(self, dwReserved):
##        '-no docstring-'
##        #return ppbData, pulSize
##
##    def SetSerializedState(self, pbData, ulSize, dwReserved):
##        '-no docstring-'
##        #return
##


class ISpeechDataKey(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechDataKey Interface"
    _iid_ = GUID("{CE17C09B-4EFA-44D5-A4C9-59D9585AB0CD}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechTokenContext'
STCInprocServer = 1
STCInprocHandler = 2
STCLocalServer = 4
STCRemoteServer = 16
STCAll = 23
SpeechTokenContext = c_int  # enum

# values for enumeration 'SpeechTokenShellFolder'
STSF_AppData = 26
STSF_LocalAppData = 28
STSF_CommonAppData = 35
STSF_FlagCreate = 32768
SpeechTokenShellFolder = c_int  # enum
ISpeechObjectToken._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Id"), "propget"],
        HRESULT,
        "Id",
        (["out", "retval"], POINTER(BSTR), "ObjectId"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("DataKey"), "hidden", "propget"],
        HRESULT,
        "DataKey",
        (["out", "retval"], POINTER(POINTER(ISpeechDataKey)), "DataKey"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Category"), "propget"],
        HRESULT,
        "Category",
        (["out", "retval"], POINTER(POINTER(ISpeechObjectTokenCategory)), "Category"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("GetDescription")],
        HRESULT,
        "GetDescription",
        (["in", "optional"], c_int, "Locale", 0),
        (["out", "retval"], POINTER(BSTR), "Description"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("SetId"), "hidden"],
        HRESULT,
        "SetId",
        (["in"], BSTR, "Id"),
        (["in", "optional"], BSTR, "CategoryID", ""),
        (["in", "optional"], VARIANT_BOOL, "CreateIfNotExist", False),
    ),
    COMMETHOD(
        [dispid(6), helpstring("GetAttribute")],
        HRESULT,
        "GetAttribute",
        (["in"], BSTR, "AttributeName"),
        (["out", "retval"], POINTER(BSTR), "AttributeValue"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("CreateInstance")],
        HRESULT,
        "CreateInstance",
        (["in", "optional"], POINTER(IUnknown), "pUnkOuter"),
        (["in", "optional"], SpeechTokenContext, "ClsContext", 23),
        (["out", "retval"], POINTER(POINTER(IUnknown)), "Object"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("Remove"), "hidden"],
        HRESULT,
        "Remove",
        (["in"], BSTR, "ObjectStorageCLSID"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("GetStorageFileName"), "hidden"],
        HRESULT,
        "GetStorageFileName",
        (["in"], BSTR, "ObjectStorageCLSID"),
        (["in"], BSTR, "KeyName"),
        (["in"], BSTR, "FileName"),
        (["in"], SpeechTokenShellFolder, "Folder"),
        (["out", "retval"], POINTER(BSTR), "FilePath"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("RemoveStorageFileName"), "hidden"],
        HRESULT,
        "RemoveStorageFileName",
        (["in"], BSTR, "ObjectStorageCLSID"),
        (["in"], BSTR, "KeyName"),
        (["in"], VARIANT_BOOL, "DeleteFile"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("IsUISupported"), "hidden"],
        HRESULT,
        "IsUISupported",
        (["in"], BSTR, "TypeOfUI"),
        (["in", "optional"], POINTER(VARIANT), "ExtraData"),
        (["in", "optional"], POINTER(IUnknown), "Object"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Supported"),
    ),
    COMMETHOD(
        [dispid(12), helpstring("DisplayUI"), "hidden"],
        HRESULT,
        "DisplayUI",
        (["in"], c_int, "hWnd"),
        (["in"], BSTR, "Title"),
        (["in"], BSTR, "TypeOfUI"),
        (["in", "optional"], POINTER(VARIANT), "ExtraData"),
        (["in", "optional"], POINTER(IUnknown), "Object"),
    ),
    COMMETHOD(
        [dispid(13), helpstring("MatchesAttributes")],
        HRESULT,
        "MatchesAttributes",
        (["in"], BSTR, "Attributes"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Matches"),
    ),
]
################################################################
## code template for ISpeechObjectToken implementation
##class ISpeechObjectToken_Impl(object):
##    @property
##    def Id(self):
##        'Id'
##        #return ObjectId
##
##    @property
##    def DataKey(self):
##        'DataKey'
##        #return DataKey
##
##    @property
##    def Category(self):
##        'Category'
##        #return Category
##
##    def GetDescription(self, Locale):
##        'GetDescription'
##        #return Description
##
##    def SetId(self, Id, CategoryID, CreateIfNotExist):
##        'SetId'
##        #return
##
##    def GetAttribute(self, AttributeName):
##        'GetAttribute'
##        #return AttributeValue
##
##    def CreateInstance(self, pUnkOuter, ClsContext):
##        'CreateInstance'
##        #return Object
##
##    def Remove(self, ObjectStorageCLSID):
##        'Remove'
##        #return
##
##    def GetStorageFileName(self, ObjectStorageCLSID, KeyName, FileName, Folder):
##        'GetStorageFileName'
##        #return FilePath
##
##    def RemoveStorageFileName(self, ObjectStorageCLSID, KeyName, DeleteFile):
##        'RemoveStorageFileName'
##        #return
##
##    def IsUISupported(self, TypeOfUI, ExtraData, Object):
##        'IsUISupported'
##        #return Supported
##
##    def DisplayUI(self, hWnd, Title, TypeOfUI, ExtraData, Object):
##        'DisplayUI'
##        #return
##
##    def MatchesAttributes(self, Attributes):
##        'MatchesAttributes'
##        #return Matches
##

SpeechCategoryVoices = (
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices"  # Constant BSTR
)


class SpSharedRecognizer(CoClass):
    "SpSharedRecognizer Class"
    _reg_clsid_ = GUID("{3BEE4890-4FE9-4A37-8C1E-5E7E12791C1F}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpSharedRecognizer._com_interfaces_ = [
    ISpeechRecognizer,
    ISpRecognizer,
    ISpRecognizer2,
    ISpRecognizer3,
    ISpSerializeState,
]


class Library(object):
    "Microsoft Speech Object Library"
    name = "SpeechLib"
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class SpLexicon(CoClass):
    "SpLexicon Class"
    _reg_clsid_ = GUID("{0655E396-25D0-11D3-9C26-00C04F8EF87C}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpLexicon._com_interfaces_ = [ISpeechLexicon, ISpLexicon, ISpPhoneticAlphabetSelection]

ISpeechDataKey._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("SetBinaryValue")],
        HRESULT,
        "SetBinaryValue",
        (["in"], BSTR, "ValueName"),
        (["in"], VARIANT, "Value"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("GetBinaryValue")],
        HRESULT,
        "GetBinaryValue",
        (["in"], BSTR, "ValueName"),
        (["out", "retval"], POINTER(VARIANT), "Value"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("SetStringValue")],
        HRESULT,
        "SetStringValue",
        (["in"], BSTR, "ValueName"),
        (["in"], BSTR, "Value"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("GetStringValue")],
        HRESULT,
        "GetStringValue",
        (["in"], BSTR, "ValueName"),
        (["out", "retval"], POINTER(BSTR), "Value"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("SetLongValue")],
        HRESULT,
        "SetLongValue",
        (["in"], BSTR, "ValueName"),
        (["in"], c_int, "Value"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("GetlongValue")],
        HRESULT,
        "GetLongValue",
        (["in"], BSTR, "ValueName"),
        (["out", "retval"], POINTER(c_int), "Value"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("OpenKey")],
        HRESULT,
        "OpenKey",
        (["in"], BSTR, "SubKeyName"),
        (["out", "retval"], POINTER(POINTER(ISpeechDataKey)), "SubKey"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("CreateKey")],
        HRESULT,
        "CreateKey",
        (["in"], BSTR, "SubKeyName"),
        (["out", "retval"], POINTER(POINTER(ISpeechDataKey)), "SubKey"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("DeleteKey")],
        HRESULT,
        "DeleteKey",
        (["in"], BSTR, "SubKeyName"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("DeleteValue")],
        HRESULT,
        "DeleteValue",
        (["in"], BSTR, "ValueName"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("EnumKeys")],
        HRESULT,
        "EnumKeys",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(BSTR), "SubKeyName"),
    ),
    COMMETHOD(
        [dispid(12), helpstring("EnumValues")],
        HRESULT,
        "EnumValues",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(BSTR), "ValueName"),
    ),
]
################################################################
## code template for ISpeechDataKey implementation
##class ISpeechDataKey_Impl(object):
##    def SetBinaryValue(self, ValueName, Value):
##        'SetBinaryValue'
##        #return
##
##    def GetBinaryValue(self, ValueName):
##        'GetBinaryValue'
##        #return Value
##
##    def SetStringValue(self, ValueName, Value):
##        'SetStringValue'
##        #return
##
##    def GetStringValue(self, ValueName):
##        'GetStringValue'
##        #return Value
##
##    def SetLongValue(self, ValueName, Value):
##        'SetLongValue'
##        #return
##
##    def GetLongValue(self, ValueName):
##        'GetlongValue'
##        #return Value
##
##    def OpenKey(self, SubKeyName):
##        'OpenKey'
##        #return SubKey
##
##    def CreateKey(self, SubKeyName):
##        'CreateKey'
##        #return SubKey
##
##    def DeleteKey(self, SubKeyName):
##        'DeleteKey'
##        #return
##
##    def DeleteValue(self, ValueName):
##        'DeleteValue'
##        #return
##
##    def EnumKeys(self, Index):
##        'EnumKeys'
##        #return SubKeyName
##
##    def EnumValues(self, Index):
##        'EnumValues'
##        #return ValueName
##

SpeechCategoryAudioOut = (
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\AudioOutput"  # Constant BSTR
)
ISpLexicon._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetPronunciations",
        (["in"], WSTRING, "pszWord"),
        (["in"], c_ushort, "LangId"),
        (["in"], c_ulong, "dwFlags"),
        (["in", "out"], POINTER(SPWORDPRONUNCIATIONLIST), "pWordPronunciationList"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "AddPronunciation",
        (["in"], WSTRING, "pszWord"),
        (["in"], c_ushort, "LangId"),
        (["in"], SPPARTOFSPEECH, "ePartOfSpeech"),
        (["in"], WSTRING, "pszPronunciation"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "RemovePronunciation",
        (["in"], WSTRING, "pszWord"),
        (["in"], c_ushort, "LangId"),
        (["in"], SPPARTOFSPEECH, "ePartOfSpeech"),
        (["in"], WSTRING, "pszPronunciation"),
    ),
    COMMETHOD(
        [], HRESULT, "GetGeneration", (["out"], POINTER(c_ulong), "pdwGeneration")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetGenerationChange",
        (["in"], c_ulong, "dwFlags"),
        (["in", "out"], POINTER(c_ulong), "pdwGeneration"),
        (["in", "out"], POINTER(SPWORDLIST), "pWordList"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetWords",
        (["in"], c_ulong, "dwFlags"),
        (["in", "out"], POINTER(c_ulong), "pdwGeneration"),
        (["in", "out"], POINTER(c_ulong), "pdwCookie"),
        (["in", "out"], POINTER(SPWORDLIST), "pWordList"),
    ),
]
################################################################
## code template for ISpLexicon implementation
##class ISpLexicon_Impl(object):
##    def GetPronunciations(self, pszWord, LangId, dwFlags):
##        '-no docstring-'
##        #return pWordPronunciationList
##
##    def AddPronunciation(self, pszWord, LangId, ePartOfSpeech, pszPronunciation):
##        '-no docstring-'
##        #return
##
##    def RemovePronunciation(self, pszWord, LangId, ePartOfSpeech, pszPronunciation):
##        '-no docstring-'
##        #return
##
##    def GetGeneration(self):
##        '-no docstring-'
##        #return pdwGeneration
##
##    def GetGenerationChange(self, dwFlags):
##        '-no docstring-'
##        #return pdwGeneration, pWordList
##
##    def GetWords(self, dwFlags):
##        '-no docstring-'
##        #return pdwGeneration, pdwCookie, pWordList
##

SpeechCategoryAudioIn = (
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\AudioInput"  # Constant BSTR
)


class ISpStreamFormatConverter(ISpStreamFormat):
    _case_insensitive_ = True
    "ISpStreamFormatConverter Interface"
    _iid_ = GUID("{678A932C-EA71-4446-9B41-78FDA6280A29}")
    _idlflags_ = ["restricted"]


ISpStreamFormatConverter._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetBaseStream",
        (["in"], POINTER(ISpStreamFormat), "pStream"),
        (["in"], c_int, "fSetFormatToBaseStreamFormat"),
        (["in"], c_int, "fWriteToBaseStream"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetBaseStream",
        (["out"], POINTER(POINTER(ISpStreamFormat)), "ppStream"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetFormat",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "rguidFormatIdOfConvertedStream",
        ),
        (["in"], POINTER(WAVEFORMATEX), "pWaveFormatExOfConvertedStream"),
    ),
    COMMETHOD([], HRESULT, "ResetSeekPosition"),
    COMMETHOD(
        [],
        HRESULT,
        "ScaleConvertedToBaseOffset",
        (["in"], c_ulonglong, "ullOffsetConvertedStream"),
        (["out"], POINTER(c_ulonglong), "pullOffsetBaseStream"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "ScaleBaseToConvertedOffset",
        (["in"], c_ulonglong, "ullOffsetBaseStream"),
        (["out"], POINTER(c_ulonglong), "pullOffsetConvertedStream"),
    ),
]
################################################################
## code template for ISpStreamFormatConverter implementation
##class ISpStreamFormatConverter_Impl(object):
##    def SetBaseStream(self, pStream, fSetFormatToBaseStreamFormat, fWriteToBaseStream):
##        '-no docstring-'
##        #return
##
##    def GetBaseStream(self):
##        '-no docstring-'
##        #return ppStream
##
##    def SetFormat(self, rguidFormatIdOfConvertedStream, pWaveFormatExOfConvertedStream):
##        '-no docstring-'
##        #return
##
##    def ResetSeekPosition(self):
##        '-no docstring-'
##        #return
##
##    def ScaleConvertedToBaseOffset(self, ullOffsetConvertedStream):
##        '-no docstring-'
##        #return pullOffsetBaseStream
##
##    def ScaleBaseToConvertedOffset(self, ullOffsetBaseStream):
##        '-no docstring-'
##        #return pullOffsetConvertedStream
##

SPSERIALIZEDPHRASE._fields_ = [
    ("ulSerializedSize", c_ulong),
]
assert sizeof(SPSERIALIZEDPHRASE) == 4, sizeof(SPSERIALIZEDPHRASE)
assert alignment(SPSERIALIZEDPHRASE) == 4, alignment(SPSERIALIZEDPHRASE)

# values for enumeration 'DISPID_SpeechPhraseAlternate'
DISPID_SPARecoResult = 1
DISPID_SPAStartElementInResult = 2
DISPID_SPANumberOfElementsInResult = 3
DISPID_SPAPhraseInfo = 4
DISPID_SPACommit = 5
DISPID_SpeechPhraseAlternate = c_int  # enum
ISpResourceManager._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetObject",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "guidServiceId",
        ),
        (["in"], POINTER(IUnknown), "punkObject"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetObject",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "guidServiceId",
        ),
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "ObjectCLSID",
        ),
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "ObjectIID",
        ),
        (["in"], c_int, "fReleaseWhenLastExternalRefReleased"),
        (["out"], POINTER(c_void_p), "ppObject"),
    ),
]
################################################################
## code template for ISpResourceManager implementation
##class ISpResourceManager_Impl(object):
##    def SetObject(self, guidServiceId, punkObject):
##        '-no docstring-'
##        #return
##
##    def GetObject(self, guidServiceId, ObjectCLSID, ObjectIID, fReleaseWhenLastExternalRefReleased):
##        '-no docstring-'
##        #return ppObject
##


# values for enumeration 'SPRULESTATE'
SPRS_INACTIVE = 0
SPRS_ACTIVE = 1
SPRS_ACTIVE_WITH_AUTO_PAUSE = 3
SPRS_ACTIVE_USER_DELIMITED = 4
SPRULESTATE = c_int  # enum


class tagSPTEXTSELECTIONINFO(Structure):
    pass


SPTEXTSELECTIONINFO = tagSPTEXTSELECTIONINFO
tagSPTEXTSELECTIONINFO._fields_ = [
    ("ulStartActiveOffset", c_ulong),
    ("cchActiveChars", c_ulong),
    ("ulStartSelection", c_ulong),
    ("cchSelection", c_ulong),
]
assert sizeof(tagSPTEXTSELECTIONINFO) == 16, sizeof(tagSPTEXTSELECTIONINFO)
assert alignment(tagSPTEXTSELECTIONINFO) == 4, alignment(tagSPTEXTSELECTIONINFO)

# values for enumeration 'DISPID_SpeechPhraseElements'
DISPID_SPEsCount = 1
DISPID_SPEsItem = 0
DISPID_SPEs_NewEnum = -4
DISPID_SpeechPhraseElements = c_int  # enum


class SpStreamFormatConverter(CoClass):
    "FormatConverter Class"
    _reg_clsid_ = GUID("{7013943A-E2EC-11D2-A086-00C04F8EF9B5}")
    _idlflags_ = ["hidden", "restricted"]
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpStreamFormatConverter._com_interfaces_ = [ISpStreamFormatConverter]


class ISpGrammarBuilder(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpGrammarBuilder Interface"
    _iid_ = GUID("{8137828F-591A-4A42-BE58-49EA7EBAAC68}")
    _idlflags_ = ["restricted"]


class ISpRecoGrammar(ISpGrammarBuilder):
    _case_insensitive_ = True
    "ISpRecoGrammar Interface"
    _iid_ = GUID("{2177DB29-7F45-47D0-8554-067E91C80502}")
    _idlflags_ = ["restricted"]


# values for enumeration 'SPGRAMMARWORDTYPE'
SPWT_DISPLAY = 0
SPWT_LEXICAL = 1
SPWT_PRONUNCIATION = 2
SPWT_LEXICAL_NO_SPECIAL_CHARS = 3
SPGRAMMARWORDTYPE = c_int  # enum


class tagSPPROPERTYINFO(Structure):
    pass


SPPROPERTYINFO = tagSPPROPERTYINFO
ISpGrammarBuilder._methods_ = [
    COMMETHOD([], HRESULT, "ResetGrammar", (["in"], c_ushort, "NewLanguage")),
    COMMETHOD(
        [],
        HRESULT,
        "GetRule",
        (["in"], WSTRING, "pszRuleName"),
        (["in"], c_ulong, "dwRuleId"),
        (["in"], c_ulong, "dwAttributes"),
        (["in"], c_int, "fCreateIfNotExist"),
        (["out"], POINTER(c_void_p), "phInitialState"),
    ),
    COMMETHOD([], HRESULT, "ClearRule", (["in"], c_void_p, "hState")),
    COMMETHOD(
        [],
        HRESULT,
        "CreateNewState",
        (["in"], c_void_p, "hState"),
        (["out"], POINTER(c_void_p), "phState"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "AddWordTransition",
        (["in"], c_void_p, "hFromState"),
        (["in"], c_void_p, "hToState"),
        (["in"], WSTRING, "psz"),
        (["in"], WSTRING, "pszSeparators"),
        (["in"], SPGRAMMARWORDTYPE, "eWordType"),
        (["in"], c_float, "Weight"),
        (["in"], POINTER(SPPROPERTYINFO), "pPropInfo"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "AddRuleTransition",
        (["in"], c_void_p, "hFromState"),
        (["in"], c_void_p, "hToState"),
        (["in"], c_void_p, "hRule"),
        (["in"], c_float, "Weight"),
        (["in"], POINTER(SPPROPERTYINFO), "pPropInfo"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "AddResource",
        (["in"], c_void_p, "hRuleState"),
        (["in"], WSTRING, "pszResourceName"),
        (["in"], WSTRING, "pszResourceValue"),
    ),
    COMMETHOD([], HRESULT, "Commit", (["in"], c_ulong, "dwReserved")),
]
################################################################
## code template for ISpGrammarBuilder implementation
##class ISpGrammarBuilder_Impl(object):
##    def ResetGrammar(self, NewLanguage):
##        '-no docstring-'
##        #return
##
##    def GetRule(self, pszRuleName, dwRuleId, dwAttributes, fCreateIfNotExist):
##        '-no docstring-'
##        #return phInitialState
##
##    def ClearRule(self, hState):
##        '-no docstring-'
##        #return
##
##    def CreateNewState(self, hState):
##        '-no docstring-'
##        #return phState
##
##    def AddWordTransition(self, hFromState, hToState, psz, pszSeparators, eWordType, Weight, pPropInfo):
##        '-no docstring-'
##        #return
##
##    def AddRuleTransition(self, hFromState, hToState, hRule, Weight, pPropInfo):
##        '-no docstring-'
##        #return
##
##    def AddResource(self, hRuleState, pszResourceName, pszResourceValue):
##        '-no docstring-'
##        #return
##
##    def Commit(self, dwReserved):
##        '-no docstring-'
##        #return
##


# values for enumeration 'SPLOADOPTIONS'
SPLO_STATIC = 0
SPLO_DYNAMIC = 1
SPLOADOPTIONS = c_int  # enum


class SPBINARYGRAMMAR(Structure):
    pass


# values for enumeration 'SPWORDPRONOUNCEABLE'
SPWP_UNKNOWN_WORD_UNPRONOUNCEABLE = 0
SPWP_UNKNOWN_WORD_PRONOUNCEABLE = 1
SPWP_KNOWN_WORD_PRONOUNCEABLE = 2
SPWORDPRONOUNCEABLE = c_int  # enum

# values for enumeration 'SPGRAMMARSTATE'
SPGS_DISABLED = 0
SPGS_ENABLED = 1
SPGS_EXCLUSIVE = 3
SPGRAMMARSTATE = c_int  # enum
ISpRecoGrammar._methods_ = [
    COMMETHOD(
        [], HRESULT, "GetGrammarId", (["out"], POINTER(c_ulonglong), "pullGrammarId")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetRecoContext",
        (["out"], POINTER(POINTER(ISpRecoContext)), "ppRecoCtxt"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadCmdFromFile",
        (["in"], WSTRING, "pszFileName"),
        (["in"], SPLOADOPTIONS, "Options"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadCmdFromObject",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "rcid",
        ),
        (["in"], WSTRING, "pszGrammarName"),
        (["in"], SPLOADOPTIONS, "Options"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadCmdFromResource",
        (["in"], c_void_p, "hModule"),
        (["in"], WSTRING, "pszResourceName"),
        (["in"], WSTRING, "pszResourceType"),
        (["in"], c_ushort, "wLanguage"),
        (["in"], SPLOADOPTIONS, "Options"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadCmdFromMemory",
        (["in"], POINTER(SPBINARYGRAMMAR), "pGrammar"),
        (["in"], SPLOADOPTIONS, "Options"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadCmdFromProprietaryGrammar",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "rguidParam",
        ),
        (["in"], WSTRING, "pszStringParam"),
        (["in"], c_void_p, "pvDataPrarm"),
        (["in"], c_ulong, "cbDataSize"),
        (["in"], SPLOADOPTIONS, "Options"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetRuleState",
        (["in"], WSTRING, "pszName"),
        (["in"], c_void_p, "pReserved"),
        (["in"], SPRULESTATE, "NewState"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetRuleIdState",
        (["in"], c_ulong, "ulRuleId"),
        (["in"], SPRULESTATE, "NewState"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadDictation",
        (["in"], WSTRING, "pszTopicName"),
        (["in"], SPLOADOPTIONS, "Options"),
    ),
    COMMETHOD([], HRESULT, "UnloadDictation"),
    COMMETHOD([], HRESULT, "SetDictationState", (["in"], SPRULESTATE, "NewState")),
    COMMETHOD(
        [],
        HRESULT,
        "SetWordSequenceData",
        (["in"], POINTER(c_ushort), "pText"),
        (["in"], c_ulong, "cchText"),
        (["in"], POINTER(SPTEXTSELECTIONINFO), "pInfo"),
    ),
    COMMETHOD(
        [], HRESULT, "SetTextSelection", (["in"], POINTER(SPTEXTSELECTIONINFO), "pInfo")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "IsPronounceable",
        (["in"], WSTRING, "pszWord"),
        (["out"], POINTER(SPWORDPRONOUNCEABLE), "pWordPronounceable"),
    ),
    COMMETHOD(
        [], HRESULT, "SetGrammarState", (["in"], SPGRAMMARSTATE, "eGrammarState")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SaveCmd",
        (["in"], POINTER(IStream), "pStream"),
        (["out", "optional"], POINTER(WSTRING), "ppszCoMemErrorText"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetGrammarState",
        (["out"], POINTER(SPGRAMMARSTATE), "peGrammarState"),
    ),
]
################################################################
## code template for ISpRecoGrammar implementation
##class ISpRecoGrammar_Impl(object):
##    def GetGrammarId(self):
##        '-no docstring-'
##        #return pullGrammarId
##
##    def GetRecoContext(self):
##        '-no docstring-'
##        #return ppRecoCtxt
##
##    def LoadCmdFromFile(self, pszFileName, Options):
##        '-no docstring-'
##        #return
##
##    def LoadCmdFromObject(self, rcid, pszGrammarName, Options):
##        '-no docstring-'
##        #return
##
##    def LoadCmdFromResource(self, hModule, pszResourceName, pszResourceType, wLanguage, Options):
##        '-no docstring-'
##        #return
##
##    def LoadCmdFromMemory(self, pGrammar, Options):
##        '-no docstring-'
##        #return
##
##    def LoadCmdFromProprietaryGrammar(self, rguidParam, pszStringParam, pvDataPrarm, cbDataSize, Options):
##        '-no docstring-'
##        #return
##
##    def SetRuleState(self, pszName, pReserved, NewState):
##        '-no docstring-'
##        #return
##
##    def SetRuleIdState(self, ulRuleId, NewState):
##        '-no docstring-'
##        #return
##
##    def LoadDictation(self, pszTopicName, Options):
##        '-no docstring-'
##        #return
##
##    def UnloadDictation(self):
##        '-no docstring-'
##        #return
##
##    def SetDictationState(self, NewState):
##        '-no docstring-'
##        #return
##
##    def SetWordSequenceData(self, pText, cchText, pInfo):
##        '-no docstring-'
##        #return
##
##    def SetTextSelection(self, pInfo):
##        '-no docstring-'
##        #return
##
##    def IsPronounceable(self, pszWord):
##        '-no docstring-'
##        #return pWordPronounceable
##
##    def SetGrammarState(self, eGrammarState):
##        '-no docstring-'
##        #return
##
##    def SaveCmd(self, pStream):
##        '-no docstring-'
##        #return ppszCoMemErrorText
##
##    def GetGrammarState(self):
##        '-no docstring-'
##        #return peGrammarState
##


# values for enumeration 'DISPID_SpeechPhraseElement'
DISPID_SPEAudioTimeOffset = 1
DISPID_SPEAudioSizeTime = 2
DISPID_SPEAudioStreamOffset = 3
DISPID_SPEAudioSizeBytes = 4
DISPID_SPERetainedStreamOffset = 5
DISPID_SPERetainedSizeBytes = 6
DISPID_SPEDisplayText = 7
DISPID_SPELexicalForm = 8
DISPID_SPEPronunciation = 9
DISPID_SPEDisplayAttributes = 10
DISPID_SPERequiredConfidence = 11
DISPID_SPEActualConfidence = 12
DISPID_SPEEngineConfidence = 13
DISPID_SpeechPhraseElement = c_int  # enum

# values for enumeration 'DISPID_SpeechPhraseBuilder'
DISPID_SPPBRestorePhraseFromMemory = 1
DISPID_SpeechPhraseBuilder = c_int  # enum

# values for enumeration 'DISPID_SpeechPhraseReplacements'
DISPID_SPRsCount = 1
DISPID_SPRsItem = 0
DISPID_SPRs_NewEnum = -4
DISPID_SpeechPhraseReplacements = c_int  # enum

# values for enumeration 'DISPID_SpeechRecoResultTimes'
DISPID_SRRTStreamTime = 1
DISPID_SRRTLength = 2
DISPID_SRRTTickCount = 3
DISPID_SRRTOffsetFromStart = 4
DISPID_SpeechRecoResultTimes = c_int  # enum

# values for enumeration 'DISPID_SpeechPhraseRule'
DISPID_SPRuleName = 1
DISPID_SPRuleId = 2
DISPID_SPRuleFirstElement = 3
DISPID_SPRuleNumberOfElements = 4
DISPID_SPRuleParent = 5
DISPID_SPRuleChildren = 6
DISPID_SPRuleConfidence = 7
DISPID_SPRuleEngineConfidence = 8
DISPID_SpeechPhraseRule = c_int  # enum

# values for enumeration 'DISPID_SpeechPhraseAlternates'
DISPID_SPAsCount = 1
DISPID_SPAsItem = 0
DISPID_SPAs_NewEnum = -4
DISPID_SpeechPhraseAlternates = c_int  # enum


class SPRECOCONTEXTSTATUS(Structure):
    pass


# values for enumeration 'SPINTERFERENCE'
SPINTERFERENCE_NONE = 0
SPINTERFERENCE_NOISE = 1
SPINTERFERENCE_NOSIGNAL = 2
SPINTERFERENCE_TOOLOUD = 3
SPINTERFERENCE_TOOQUIET = 4
SPINTERFERENCE_TOOFAST = 5
SPINTERFERENCE_TOOSLOW = 6
SPINTERFERENCE_LATENCY_WARNING = 7
SPINTERFERENCE_LATENCY_TRUNCATE_BEGIN = 8
SPINTERFERENCE_LATENCY_TRUNCATE_END = 9
SPINTERFERENCE = c_int  # enum
SPRECOCONTEXTSTATUS._fields_ = [
    ("eInterference", SPINTERFERENCE),
    ("szRequestTypeOfUI", c_ushort * 255),
    ("dwReserved1", c_ulong),
    ("dwReserved2", c_ulong),
]
assert sizeof(SPRECOCONTEXTSTATUS) == 524, sizeof(SPRECOCONTEXTSTATUS)
assert alignment(SPRECOCONTEXTSTATUS) == 4, alignment(SPRECOCONTEXTSTATUS)
tagSPPROPERTYINFO._fields_ = [
    ("pszName", WSTRING),
    ("ulId", c_ulong),
    ("pszValue", WSTRING),
    ("vValue", VARIANT),
]
assert sizeof(tagSPPROPERTYINFO) == 32, sizeof(tagSPPROPERTYINFO)
assert alignment(tagSPPROPERTYINFO) == 8, alignment(tagSPPROPERTYINFO)

# values for enumeration 'DISPID_SpeechPhraseInfo'
DISPID_SPILanguageId = 1
DISPID_SPIGrammarId = 2
DISPID_SPIStartTime = 3
DISPID_SPIAudioStreamPosition = 4
DISPID_SPIAudioSizeBytes = 5
DISPID_SPIRetainedSizeBytes = 6
DISPID_SPIAudioSizeTime = 7
DISPID_SPIRule = 8
DISPID_SPIProperties = 9
DISPID_SPIElements = 10
DISPID_SPIReplacements = 11
DISPID_SPIEngineId = 12
DISPID_SPIEnginePrivateData = 13
DISPID_SPISaveToMemory = 14
DISPID_SPIGetText = 15
DISPID_SPIGetDisplayAttributes = 16
DISPID_SpeechPhraseInfo = c_int  # enum

# values for enumeration 'SPAUDIOOPTIONS'
SPAO_NONE = 0
SPAO_RETAIN_AUDIO = 1
SPAUDIOOPTIONS = c_int  # enum


class ISpeechPhoneConverter(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhoneConverter Interface"
    _iid_ = GUID("{C3E4F353-433F-43D6-89A1-6A62A7054C3D}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechPhoneConverter._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("LanguageId"), "propget"],
        HRESULT,
        "LanguageId",
        (["out", "retval"], POINTER(c_int), "LanguageId"),
    ),
    COMMETHOD(
        [dispid(1), helpstring("LanguageId"), "propput"],
        HRESULT,
        "LanguageId",
        (["in"], c_int, "LanguageId"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("PhoneToId")],
        HRESULT,
        "PhoneToId",
        (["in"], BSTR, "Phonemes"),
        (["out", "retval"], POINTER(VARIANT), "IdArray"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("IdToPhone")],
        HRESULT,
        "IdToPhone",
        (["in"], VARIANT, "IdArray"),
        (["out", "retval"], POINTER(BSTR), "Phonemes"),
    ),
]
################################################################
## code template for ISpeechPhoneConverter implementation
##class ISpeechPhoneConverter_Impl(object):
##    def _get(self):
##        'LanguageId'
##        #return LanguageId
##    def _set(self, LanguageId):
##        'LanguageId'
##    LanguageId = property(_get, _set, doc = _set.__doc__)
##
##    def PhoneToId(self, Phonemes):
##        'PhoneToId'
##        #return IdArray
##
##    def IdToPhone(self, IdArray):
##        'IdToPhone'
##        #return Phonemes
##


class ISpRecoResult(ISpPhrase):
    _case_insensitive_ = True
    "ISpRecoResult Interface"
    _iid_ = GUID("{20B053BE-E235-43CD-9A2A-8D17A48B7842}")
    _idlflags_ = ["restricted"]


class SPRECORESULTTIMES(Structure):
    pass


class ISpPhraseAlt(ISpPhrase):
    _case_insensitive_ = True
    "ISpPhraseAlt Interface"
    _iid_ = GUID("{8FCEBC98-4E49-4067-9C6C-D86A0E092E3D}")
    _idlflags_ = ["restricted"]


class SPSERIALIZEDRESULT(Structure):
    pass


ISpRecoResult._methods_ = [
    COMMETHOD(
        [], HRESULT, "GetResultTimes", (["out"], POINTER(SPRECORESULTTIMES), "pTimes")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetAlternates",
        (["in"], c_ulong, "ulStartElement"),
        (["in"], c_ulong, "cElements"),
        (["in"], c_ulong, "ulRequestCount"),
        (["out"], POINTER(POINTER(ISpPhraseAlt)), "ppPhrases"),
        (["out"], POINTER(c_ulong), "pcPhrasesReturned"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetAudio",
        (["in"], c_ulong, "ulStartElement"),
        (["in"], c_ulong, "cElements"),
        (["out"], POINTER(POINTER(ISpStreamFormat)), "ppStream"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SpeakAudio",
        (["in"], c_ulong, "ulStartElement"),
        (["in"], c_ulong, "cElements"),
        (["in"], c_ulong, "dwFlags"),
        (["out"], POINTER(c_ulong), "pulStreamNumber"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "Serialize",
        (["out"], POINTER(POINTER(SPSERIALIZEDRESULT)), "ppCoMemSerializedResult"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "ScaleAudio",
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pAudioFormatId",
        ),
        (["in"], POINTER(WAVEFORMATEX), "pWaveFormatEx"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetRecoContext",
        (["out"], POINTER(POINTER(ISpRecoContext)), "ppRecoContext"),
    ),
]
################################################################
## code template for ISpRecoResult implementation
##class ISpRecoResult_Impl(object):
##    def GetResultTimes(self):
##        '-no docstring-'
##        #return pTimes
##
##    def GetAlternates(self, ulStartElement, cElements, ulRequestCount):
##        '-no docstring-'
##        #return ppPhrases, pcPhrasesReturned
##
##    def GetAudio(self, ulStartElement, cElements):
##        '-no docstring-'
##        #return ppStream
##
##    def SpeakAudio(self, ulStartElement, cElements, dwFlags):
##        '-no docstring-'
##        #return pulStreamNumber
##
##    def Serialize(self):
##        '-no docstring-'
##        #return ppCoMemSerializedResult
##
##    def ScaleAudio(self, pAudioFormatId, pWaveFormatEx):
##        '-no docstring-'
##        #return
##
##    def GetRecoContext(self):
##        '-no docstring-'
##        #return ppRecoContext
##

SPSERIALIZEDRESULT._fields_ = [
    ("ulSerializedSize", c_ulong),
]
assert sizeof(SPSERIALIZEDRESULT) == 4, sizeof(SPSERIALIZEDRESULT)
assert alignment(SPSERIALIZEDRESULT) == 4, alignment(SPSERIALIZEDRESULT)

# values for enumeration 'DISPID_SpeechPhraseReplacement'
DISPID_SPRDisplayAttributes = 1
DISPID_SPRText = 2
DISPID_SPRFirstElement = 3
DISPID_SPRNumberOfElements = 4
DISPID_SpeechPhraseReplacement = c_int  # enum
ISpPhraseAlt._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetAltInfo",
        (["out"], POINTER(POINTER(ISpPhrase)), "ppParent"),
        (["out"], POINTER(c_ulong), "pulStartElementInParent"),
        (["out"], POINTER(c_ulong), "pcElementsInParent"),
        (["out"], POINTER(c_ulong), "pcElementsInAlt"),
    ),
    COMMETHOD([], HRESULT, "Commit"),
]
################################################################
## code template for ISpPhraseAlt implementation
##class ISpPhraseAlt_Impl(object):
##    def GetAltInfo(self):
##        '-no docstring-'
##        #return ppParent, pulStartElementInParent, pcElementsInParent, pcElementsInAlt
##
##    def Commit(self):
##        '-no docstring-'
##        #return
##


# values for enumeration 'DISPID_SpeechPhraseProperty'
DISPID_SPPName = 1
DISPID_SPPId = 2
DISPID_SPPValue = 3
DISPID_SPPFirstElement = 4
DISPID_SPPNumberOfElements = 5
DISPID_SPPEngineConfidence = 6
DISPID_SPPConfidence = 7
DISPID_SPPParent = 8
DISPID_SPPChildren = 9
DISPID_SpeechPhraseProperty = c_int  # enum
SPRECORESULTTIMES._fields_ = [
    ("ftStreamTime", _FILETIME),
    ("ullLength", c_ulonglong),
    ("dwTickCount", c_ulong),
    ("ullStart", c_ulonglong),
]
assert sizeof(SPRECORESULTTIMES) == 32, sizeof(SPRECORESULTTIMES)
assert alignment(SPRECORESULTTIMES) == 8, alignment(SPRECORESULTTIMES)
tagSTATSTG._fields_ = [
    ("pwcsName", WSTRING),
    ("Type", c_ulong),
    ("cbSize", _ULARGE_INTEGER),
    ("mtime", _FILETIME),
    ("ctime", _FILETIME),
    ("atime", _FILETIME),
    ("grfMode", c_ulong),
    ("grfLocksSupported", c_ulong),
    ("clsid", comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
    ("grfStateBits", c_ulong),
    ("reserved", c_ulong),
]
assert sizeof(tagSTATSTG) == 72, sizeof(tagSTATSTG)
assert alignment(tagSTATSTG) == 8, alignment(tagSTATSTG)

# values for enumeration 'DISPID_SpeechPhraseProperties'
DISPID_SPPsCount = 1
DISPID_SPPsItem = 0
DISPID_SPPs_NewEnum = -4
DISPID_SpeechPhraseProperties = c_int  # enum
SPBINARYGRAMMAR._fields_ = [
    ("ulTotalSerializedSize", c_ulong),
]
assert sizeof(SPBINARYGRAMMAR) == 4, sizeof(SPBINARYGRAMMAR)
assert alignment(SPBINARYGRAMMAR) == 4, alignment(SPBINARYGRAMMAR)


class ISpeechVoiceStatus(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechVoiceStatus Interface"
    _iid_ = GUID("{8BE47B07-57F6-11D2-9EEE-00C04F797396}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechVoiceEvents'
SVEStartInputStream = 2
SVEEndInputStream = 4
SVEVoiceChange = 8
SVEBookmark = 16
SVEWordBoundary = 32
SVEPhoneme = 64
SVESentenceBoundary = 128
SVEViseme = 256
SVEAudioLevel = 512
SVEPrivate = 32768
SVEAllEvents = 33790
SpeechVoiceEvents = c_int  # enum

# values for enumeration 'SpeechVoicePriority'
SVPNormal = 0
SVPAlert = 1
SVPOver = 2
SpeechVoicePriority = c_int  # enum


class ISpeechObjectTokens(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechObjectTokens Interface"
    _iid_ = GUID("{9285B776-2E7B-4BC0-B53E-580EB6FA967F}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechVoice._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Status"), "propget"],
        HRESULT,
        "Status",
        (["out", "retval"], POINTER(POINTER(ISpeechVoiceStatus)), "Status"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Voice"), "propget"],
        HRESULT,
        "Voice",
        (["out", "retval"], POINTER(POINTER(ISpeechObjectToken)), "Voice"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Voice"), "propputref"],
        HRESULT,
        "Voice",
        (["in"], POINTER(ISpeechObjectToken), "Voice"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Gets the audio output object"), "propget"],
        HRESULT,
        "AudioOutput",
        (["out", "retval"], POINTER(POINTER(ISpeechObjectToken)), "AudioOutput"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Gets the audio output object"), "propputref"],
        HRESULT,
        "AudioOutput",
        (["in"], POINTER(ISpeechObjectToken), "AudioOutput"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Gets the audio output stream"), "propget"],
        HRESULT,
        "AudioOutputStream",
        (["out", "retval"], POINTER(POINTER(ISpeechBaseStream)), "AudioOutputStream"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Gets the audio output stream"), "propputref"],
        HRESULT,
        "AudioOutputStream",
        (["in"], POINTER(ISpeechBaseStream), "AudioOutputStream"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("Rate"), "propget"],
        HRESULT,
        "Rate",
        (["out", "retval"], POINTER(c_int), "Rate"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("Rate"), "propput"],
        HRESULT,
        "Rate",
        (["in"], c_int, "Rate"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("Volume"), "propget"],
        HRESULT,
        "Volume",
        (["out", "retval"], POINTER(c_int), "Volume"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("Volume"), "propput"],
        HRESULT,
        "Volume",
        (["in"], c_int, "Volume"),
    ),
    COMMETHOD(
        [
            dispid(7),
            helpstring("AllowAudioOutputFormatChangesOnNextSet"),
            "hidden",
            "propput",
        ],
        HRESULT,
        "AllowAudioOutputFormatChangesOnNextSet",
        (["in"], VARIANT_BOOL, "Allow"),
    ),
    COMMETHOD(
        [
            dispid(7),
            helpstring("AllowAudioOutputFormatChangesOnNextSet"),
            "hidden",
            "propget",
        ],
        HRESULT,
        "AllowAudioOutputFormatChangesOnNextSet",
        (["out", "retval"], POINTER(VARIANT_BOOL), "Allow"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("EventInterests"), "propget"],
        HRESULT,
        "EventInterests",
        (["out", "retval"], POINTER(SpeechVoiceEvents), "EventInterestFlags"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("EventInterests"), "propput"],
        HRESULT,
        "EventInterests",
        (["in"], SpeechVoiceEvents, "EventInterestFlags"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("Priority"), "propput"],
        HRESULT,
        "Priority",
        (["in"], SpeechVoicePriority, "Priority"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("Priority"), "propget"],
        HRESULT,
        "Priority",
        (["out", "retval"], POINTER(SpeechVoicePriority), "Priority"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("AlertBoundary"), "propput"],
        HRESULT,
        "AlertBoundary",
        (["in"], SpeechVoiceEvents, "Boundary"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("AlertBoundary"), "propget"],
        HRESULT,
        "AlertBoundary",
        (["out", "retval"], POINTER(SpeechVoiceEvents), "Boundary"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("SyncSpeakTimeout"), "propput"],
        HRESULT,
        "SynchronousSpeakTimeout",
        (["in"], c_int, "msTimeout"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("SyncSpeakTimeout"), "propget"],
        HRESULT,
        "SynchronousSpeakTimeout",
        (["out", "retval"], POINTER(c_int), "msTimeout"),
    ),
    COMMETHOD(
        [dispid(12), helpstring("Speak")],
        HRESULT,
        "Speak",
        (["in"], BSTR, "Text"),
        (["in", "optional"], SpeechVoiceSpeakFlags, "Flags", 0),
        (["out", "retval"], POINTER(c_int), "StreamNumber"),
    ),
    COMMETHOD(
        [dispid(13), helpstring("SpeakStream")],
        HRESULT,
        "SpeakStream",
        (["in"], POINTER(ISpeechBaseStream), "Stream"),
        (["in", "optional"], SpeechVoiceSpeakFlags, "Flags", 0),
        (["out", "retval"], POINTER(c_int), "StreamNumber"),
    ),
    COMMETHOD(
        [dispid(14), helpstring("Pauses the voices rendering.")], HRESULT, "Pause"
    ),
    COMMETHOD(
        [dispid(15), helpstring("Resumes the voices rendering.")], HRESULT, "Resume"
    ),
    COMMETHOD(
        [dispid(16), helpstring("Skips rendering the specified number of items.")],
        HRESULT,
        "Skip",
        (["in"], BSTR, "Type"),
        (["in"], c_int, "NumItems"),
        (["out", "retval"], POINTER(c_int), "NumSkipped"),
    ),
    COMMETHOD(
        [dispid(17), helpstring("GetVoices")],
        HRESULT,
        "GetVoices",
        (["in", "optional"], BSTR, "RequiredAttributes", ""),
        (["in", "optional"], BSTR, "OptionalAttributes", ""),
        (["out", "retval"], POINTER(POINTER(ISpeechObjectTokens)), "ObjectTokens"),
    ),
    COMMETHOD(
        [dispid(18), helpstring("GetAudioOutputs")],
        HRESULT,
        "GetAudioOutputs",
        (["in", "optional"], BSTR, "RequiredAttributes", ""),
        (["in", "optional"], BSTR, "OptionalAttributes", ""),
        (["out", "retval"], POINTER(POINTER(ISpeechObjectTokens)), "ObjectTokens"),
    ),
    COMMETHOD(
        [dispid(19), helpstring("WaitUntilDone")],
        HRESULT,
        "WaitUntilDone",
        (["in"], c_int, "msTimeout"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Done"),
    ),
    COMMETHOD(
        [dispid(20), helpstring("SpeakCompleteEvent"), "hidden"],
        HRESULT,
        "SpeakCompleteEvent",
        (["out", "retval"], POINTER(c_int), "Handle"),
    ),
    COMMETHOD(
        [dispid(21), helpstring("IsUISupported")],
        HRESULT,
        "IsUISupported",
        (["in"], BSTR, "TypeOfUI"),
        (["in", "optional"], POINTER(VARIANT), "ExtraData"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Supported"),
    ),
    COMMETHOD(
        [dispid(22), helpstring("DisplayUI")],
        HRESULT,
        "DisplayUI",
        (["in"], c_int, "hWndParent"),
        (["in"], BSTR, "Title"),
        (["in"], BSTR, "TypeOfUI"),
        (["in", "optional"], POINTER(VARIANT), "ExtraData"),
    ),
]
################################################################
## code template for ISpeechVoice implementation
##class ISpeechVoice_Impl(object):
##    @property
##    def Status(self):
##        'Status'
##        #return Status
##
##    def Voice(self, Voice):
##        'Voice'
##        #return
##
##    def AudioOutput(self, AudioOutput):
##        'Gets the audio output object'
##        #return
##
##    def AudioOutputStream(self, AudioOutputStream):
##        'Gets the audio output stream'
##        #return
##
##    def _get(self):
##        'Rate'
##        #return Rate
##    def _set(self, Rate):
##        'Rate'
##    Rate = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'Volume'
##        #return Volume
##    def _set(self, Volume):
##        'Volume'
##    Volume = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'AllowAudioOutputFormatChangesOnNextSet'
##        #return Allow
##    def _set(self, Allow):
##        'AllowAudioOutputFormatChangesOnNextSet'
##    AllowAudioOutputFormatChangesOnNextSet = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'EventInterests'
##        #return EventInterestFlags
##    def _set(self, EventInterestFlags):
##        'EventInterests'
##    EventInterests = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'Priority'
##        #return Priority
##    def _set(self, Priority):
##        'Priority'
##    Priority = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'AlertBoundary'
##        #return Boundary
##    def _set(self, Boundary):
##        'AlertBoundary'
##    AlertBoundary = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'SyncSpeakTimeout'
##        #return msTimeout
##    def _set(self, msTimeout):
##        'SyncSpeakTimeout'
##    SynchronousSpeakTimeout = property(_get, _set, doc = _set.__doc__)
##
##    def Speak(self, Text, Flags):
##        'Speak'
##        #return StreamNumber
##
##    def SpeakStream(self, Stream, Flags):
##        'SpeakStream'
##        #return StreamNumber
##
##    def Pause(self):
##        'Pauses the voices rendering.'
##        #return
##
##    def Resume(self):
##        'Resumes the voices rendering.'
##        #return
##
##    def Skip(self, Type, NumItems):
##        'Skips rendering the specified number of items.'
##        #return NumSkipped
##
##    def GetVoices(self, RequiredAttributes, OptionalAttributes):
##        'GetVoices'
##        #return ObjectTokens
##
##    def GetAudioOutputs(self, RequiredAttributes, OptionalAttributes):
##        'GetAudioOutputs'
##        #return ObjectTokens
##
##    def WaitUntilDone(self, msTimeout):
##        'WaitUntilDone'
##        #return Done
##
##    def SpeakCompleteEvent(self):
##        'SpeakCompleteEvent'
##        #return Handle
##
##    def IsUISupported(self, TypeOfUI, ExtraData):
##        'IsUISupported'
##        #return Supported
##
##    def DisplayUI(self, hWndParent, Title, TypeOfUI, ExtraData):
##        'DisplayUI'
##        #return
##


# values for enumeration 'DISPID_SpeechRecoContextEvents'
DISPID_SRCEStartStream = 1
DISPID_SRCEEndStream = 2
DISPID_SRCEBookmark = 3
DISPID_SRCESoundStart = 4
DISPID_SRCESoundEnd = 5
DISPID_SRCEPhraseStart = 6
DISPID_SRCERecognition = 7
DISPID_SRCEHypothesis = 8
DISPID_SRCEPropertyNumberChange = 9
DISPID_SRCEPropertyStringChange = 10
DISPID_SRCEFalseRecognition = 11
DISPID_SRCEInterference = 12
DISPID_SRCERequestUI = 13
DISPID_SRCERecognizerStateChange = 14
DISPID_SRCEAdaptation = 15
DISPID_SRCERecognitionForOtherContext = 16
DISPID_SRCEAudioLevel = 17
DISPID_SRCEEnginePrivate = 18
DISPID_SpeechRecoContextEvents = c_int  # enum

# values for enumeration 'DISPID_SpeechGrammarRules'
DISPID_SGRsCount = 1
DISPID_SGRsDynamic = 2
DISPID_SGRsAdd = 3
DISPID_SGRsCommit = 4
DISPID_SGRsCommitAndSave = 5
DISPID_SGRsFindRule = 6
DISPID_SGRsItem = 0
DISPID_SGRs_NewEnum = -4
DISPID_SpeechGrammarRules = c_int  # enum

# values for enumeration 'DISPID_SpeechGrammarRuleStateTransition'
DISPID_SGRSTType = 1
DISPID_SGRSTText = 2
DISPID_SGRSTRule = 3
DISPID_SGRSTWeight = 4
DISPID_SGRSTPropertyName = 5
DISPID_SGRSTPropertyId = 6
DISPID_SGRSTPropertyValue = 7
DISPID_SGRSTNextState = 8
DISPID_SpeechGrammarRuleStateTransition = c_int  # enum

# values for enumeration 'DISPID_SpeechGrammarRule'
DISPID_SGRAttributes = 1
DISPID_SGRInitialState = 2
DISPID_SGRName = 3
DISPID_SGRId = 4
DISPID_SGRClear = 5
DISPID_SGRAddResource = 6
DISPID_SGRAddState = 7
DISPID_SpeechGrammarRule = c_int  # enum


class SPRULE(Structure):
    pass


SPRULE._fields_ = [
    ("pszRuleName", WSTRING),
    ("ulRuleId", c_ulong),
    ("dwAttributes", c_ulong),
]
assert sizeof(SPRULE) == 12, sizeof(SPRULE)
assert alignment(SPRULE) == 4, alignment(SPRULE)
WAVEFORMATEX._fields_ = [
    ("wFormatTag", c_ushort),
    ("nChannels", c_ushort),
    ("nSamplesPerSec", c_ulong),
    ("nAvgBytesPerSec", c_ulong),
    ("nBlockAlign", c_ushort),
    ("wBitsPerSample", c_ushort),
    ("cbSize", c_ushort),
]
assert sizeof(WAVEFORMATEX) == 20, sizeof(WAVEFORMATEX)
assert alignment(WAVEFORMATEX) == 4, alignment(WAVEFORMATEX)


class ISpeechResourceLoader(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechResourceLoader Interface"
    _iid_ = GUID("{B9AC5783-FCD0-4B21-B119-B4F8DA8FD2C3}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechResourceLoader._methods_ = [
    COMMETHOD(
        [dispid(1)],
        HRESULT,
        "LoadResource",
        (["in"], BSTR, "bstrResourceUri"),
        (["in"], VARIANT_BOOL, "fAlwaysReload"),
        (["out"], POINTER(POINTER(IUnknown)), "pStream"),
        (["out"], POINTER(BSTR), "pbstrMIMEType"),
        (["out"], POINTER(VARIANT_BOOL), "pfModified"),
        (["out"], POINTER(BSTR), "pbstrRedirectUrl"),
    ),
    COMMETHOD(
        [dispid(2)],
        HRESULT,
        "GetLocalCopy",
        (["in"], BSTR, "bstrResourceUri"),
        (["out"], POINTER(BSTR), "pbstrLocalPath"),
        (["out"], POINTER(BSTR), "pbstrMIMEType"),
        (["out"], POINTER(BSTR), "pbstrRedirectUrl"),
    ),
    COMMETHOD(
        [dispid(3)], HRESULT, "ReleaseLocalCopy", (["in"], BSTR, "pbstrLocalPath")
    ),
]
################################################################
## code template for ISpeechResourceLoader implementation
##class ISpeechResourceLoader_Impl(object):
##    def LoadResource(self, bstrResourceUri, fAlwaysReload):
##        '-no docstring-'
##        #return pStream, pbstrMIMEType, pfModified, pbstrRedirectUrl
##
##    def GetLocalCopy(self, bstrResourceUri):
##        '-no docstring-'
##        #return pbstrLocalPath, pbstrMIMEType, pbstrRedirectUrl
##
##    def ReleaseLocalCopy(self, pbstrLocalPath):
##        '-no docstring-'
##        #return
##


class ISpeechAudioStatus(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechAudioStatus Interface"
    _iid_ = GUID("{C62D9C91-7458-47F6-862D-1EF86FB0B278}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechAudioState'
SASClosed = 0
SASStop = 1
SASPause = 2
SASRun = 3
SpeechAudioState = c_int  # enum
ISpeechAudioStatus._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("FreeBufferSpace"), "propget"],
        HRESULT,
        "FreeBufferSpace",
        (["out", "retval"], POINTER(c_int), "FreeBufferSpace"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("NonBlockingIO"), "propget"],
        HRESULT,
        "NonBlockingIO",
        (["out", "retval"], POINTER(c_int), "NonBlockingIO"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("State"), "propget"],
        HRESULT,
        "State",
        (["out", "retval"], POINTER(SpeechAudioState), "State"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("CurrentSeekPosition"), "propget"],
        HRESULT,
        "CurrentSeekPosition",
        (["out", "retval"], POINTER(VARIANT), "CurrentSeekPosition"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("CurrentDevicePosition"), "propget"],
        HRESULT,
        "CurrentDevicePosition",
        (["out", "retval"], POINTER(VARIANT), "CurrentDevicePosition"),
    ),
]
################################################################
## code template for ISpeechAudioStatus implementation
##class ISpeechAudioStatus_Impl(object):
##    @property
##    def FreeBufferSpace(self):
##        'FreeBufferSpace'
##        #return FreeBufferSpace
##
##    @property
##    def NonBlockingIO(self):
##        'NonBlockingIO'
##        #return NonBlockingIO
##
##    @property
##    def State(self):
##        'State'
##        #return State
##
##    @property
##    def CurrentSeekPosition(self):
##        'CurrentSeekPosition'
##        #return CurrentSeekPosition
##
##    @property
##    def CurrentDevicePosition(self):
##        'CurrentDevicePosition'
##        #return CurrentDevicePosition
##


class SpMMAudioEnum(CoClass):
    "SpMMAudioEnum Class"
    _reg_clsid_ = GUID("{AB1890A0-E91F-11D2-BB91-00C04F8EE6C0}")
    _idlflags_ = ["hidden", "restricted"]
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpMMAudioEnum._com_interfaces_ = [IEnumSpObjectTokens]


class IInternetSecurityManager(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "IInternetSecurityManager Interface"
    _iid_ = GUID("{79EAC9EE-BAF9-11CE-8C82-00AA004BA90B}")
    _idlflags_ = []


class IInternetSecurityMgrSite(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "IInternetSecurityMgrSite Interface"
    _iid_ = GUID("{79EAC9ED-BAF9-11CE-8C82-00AA004BA90B}")
    _idlflags_ = []


class IEnumString(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID("{00000101-0000-0000-C000-000000000046}")
    _idlflags_ = []


IInternetSecurityManager._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "SetSecuritySite",
        (["in"], POINTER(IInternetSecurityMgrSite), "pSite"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetSecuritySite",
        (["out"], POINTER(POINTER(IInternetSecurityMgrSite)), "ppSite"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "MapUrlToZone",
        (["in"], WSTRING, "pwszUrl"),
        (["out"], POINTER(c_ulong), "pdwZone"),
        (["in"], c_ulong, "dwFlags"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetSecurityId",
        (["in"], WSTRING, "pwszUrl"),
        (["out"], POINTER(c_ubyte), "pbSecurityId"),
        (["in", "out"], POINTER(c_ulong), "pcbSecurityId"),
        (["in"], ULONG_PTR, "dwReserved"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "ProcessUrlAction",
        (["in"], WSTRING, "pwszUrl"),
        (["in"], c_ulong, "dwAction"),
        (["out"], POINTER(c_ubyte), "pPolicy"),
        (["in"], c_ulong, "cbPolicy"),
        (["in"], POINTER(c_ubyte), "pContext"),
        (["in"], c_ulong, "cbContext"),
        (["in"], c_ulong, "dwFlags"),
        (["in"], c_ulong, "dwReserved"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "QueryCustomPolicy",
        (["in"], WSTRING, "pwszUrl"),
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "guidKey",
        ),
        (["out"], POINTER(POINTER(c_ubyte)), "ppPolicy"),
        (["out"], POINTER(c_ulong), "pcbPolicy"),
        (["in"], POINTER(c_ubyte), "pContext"),
        (["in"], c_ulong, "cbContext"),
        (["in"], c_ulong, "dwReserved"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetZoneMapping",
        (["in"], c_ulong, "dwZone"),
        (["in"], WSTRING, "lpszPattern"),
        (["in"], c_ulong, "dwFlags"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetZoneMappings",
        (["in"], c_ulong, "dwZone"),
        (["out"], POINTER(POINTER(IEnumString)), "ppenumString"),
        (["in"], c_ulong, "dwFlags"),
    ),
]
################################################################
## code template for IInternetSecurityManager implementation
##class IInternetSecurityManager_Impl(object):
##    def SetSecuritySite(self, pSite):
##        '-no docstring-'
##        #return
##
##    def GetSecuritySite(self):
##        '-no docstring-'
##        #return ppSite
##
##    def MapUrlToZone(self, pwszUrl, dwFlags):
##        '-no docstring-'
##        #return pdwZone
##
##    def GetSecurityId(self, pwszUrl, dwReserved):
##        '-no docstring-'
##        #return pbSecurityId, pcbSecurityId
##
##    def ProcessUrlAction(self, pwszUrl, dwAction, cbPolicy, pContext, cbContext, dwFlags, dwReserved):
##        '-no docstring-'
##        #return pPolicy
##
##    def QueryCustomPolicy(self, pwszUrl, guidKey, pContext, cbContext, dwReserved):
##        '-no docstring-'
##        #return ppPolicy, pcbPolicy
##
##    def SetZoneMapping(self, dwZone, lpszPattern, dwFlags):
##        '-no docstring-'
##        #return
##
##    def GetZoneMappings(self, dwZone, dwFlags):
##        '-no docstring-'
##        #return ppenumString
##

ISpEventSink._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "AddEvents",
        (["in"], POINTER(SPEVENT), "pEventArray"),
        (["in"], c_ulong, "ulCount"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetEventInterest",
        (["out"], POINTER(c_ulonglong), "pullEventInterest"),
    ),
]
################################################################
## code template for ISpEventSink implementation
##class ISpEventSink_Impl(object):
##    def AddEvents(self, pEventArray, ulCount):
##        '-no docstring-'
##        #return
##
##    def GetEventInterest(self):
##        '-no docstring-'
##        #return pullEventInterest
##


# values for enumeration 'DISPID_SpeechGrammarRuleState'
DISPID_SGRSRule = 1
DISPID_SGRSTransitions = 2
DISPID_SGRSAddWordTransition = 3
DISPID_SGRSAddRuleTransition = 4
DISPID_SGRSAddSpecialTransition = 5
DISPID_SpeechGrammarRuleState = c_int  # enum


class SpMMAudioIn(CoClass):
    "SpMMAudioIn Class"
    _reg_clsid_ = GUID("{CF3D2E50-53F2-11D2-960C-00C04F8EE628}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpMMAudioIn._com_interfaces_ = [
    ISpeechMMSysAudio,
    ISpEventSource,
    ISpEventSink,
    ISpObjectWithToken,
    ISpMMSysAudio,
]


# values for enumeration 'DISPID_SpeechRecoResult'
DISPID_SRRRecoContext = 1
DISPID_SRRTimes = 2
DISPID_SRRAudioFormat = 3
DISPID_SRRPhraseInfo = 4
DISPID_SRRAlternates = 5
DISPID_SRRAudio = 6
DISPID_SRRSpeakAudio = 7
DISPID_SRRSaveToMemory = 8
DISPID_SRRDiscardResultInfo = 9
DISPID_SpeechRecoResult = c_int  # enum
IInternetSecurityMgrSite._methods_ = [
    COMMETHOD([], HRESULT, "GetWindow", (["out"], POINTER(wireHWND), "phwnd")),
    COMMETHOD([], HRESULT, "EnableModeless", (["in"], c_int, "fEnable")),
]
################################################################
## code template for IInternetSecurityMgrSite implementation
##class IInternetSecurityMgrSite_Impl(object):
##    def GetWindow(self):
##        '-no docstring-'
##        #return phwnd
##
##    def EnableModeless(self, fEnable):
##        '-no docstring-'
##        #return
##


# values for enumeration 'DISPIDSPTSI'
DISPIDSPTSI_ActiveOffset = 1
DISPIDSPTSI_ActiveLength = 2
DISPIDSPTSI_SelectionOffset = 3
DISPIDSPTSI_SelectionLength = 4
DISPIDSPTSI = c_int  # enum

# values for enumeration 'DISPID_SpeechXMLRecoResult'
DISPID_SRRGetXMLResult = 10
DISPID_SRRGetXMLErrorInfo = 11
DISPID_SpeechXMLRecoResult = c_int  # enum
SPEVENT._fields_ = [
    ("eEventId", c_ushort),
    ("elParamType", c_ushort),
    ("ulStreamNum", c_ulong),
    ("ullAudioStreamOffset", c_ulonglong),
    ("wParam", UINT_PTR),
    ("lParam", LONG_PTR),
]
assert sizeof(SPEVENT) == 24, sizeof(SPEVENT)
assert alignment(SPEVENT) == 8, alignment(SPEVENT)
ISpObjectWithToken._methods_ = [
    COMMETHOD(
        [], HRESULT, "SetObjectToken", (["in"], POINTER(ISpObjectToken), "pToken")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetObjectToken",
        (["out"], POINTER(POINTER(ISpObjectToken)), "ppToken"),
    ),
]
################################################################
## code template for ISpObjectWithToken implementation
##class ISpObjectWithToken_Impl(object):
##    def SetObjectToken(self, pToken):
##        '-no docstring-'
##        #return
##
##    def GetObjectToken(self):
##        '-no docstring-'
##        #return ppToken
##


class ISpeechPhraseInfoBuilder(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechPhraseInfoBuilder Interface"
    _iid_ = GUID("{3B151836-DF3A-4E0A-846C-D2ADC9334333}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechPhraseInfoBuilder._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("RestorePhraseFromMemory")],
        HRESULT,
        "RestorePhraseFromMemory",
        (["in"], POINTER(VARIANT), "PhraseInMemory"),
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseInfo)), "PhraseInfo"),
    ),
]
################################################################
## code template for ISpeechPhraseInfoBuilder implementation
##class ISpeechPhraseInfoBuilder_Impl(object):
##    def RestorePhraseFromMemory(self, PhraseInMemory):
##        'RestorePhraseFromMemory'
##        #return PhraseInfo
##

IEnumString._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "RemoteNext",
        (["in"], c_ulong, "celt"),
        (["out"], POINTER(WSTRING), "rgelt"),
        (["out"], POINTER(c_ulong), "pceltFetched"),
    ),
    COMMETHOD([], HRESULT, "Skip", (["in"], c_ulong, "celt")),
    COMMETHOD([], HRESULT, "Reset"),
    COMMETHOD([], HRESULT, "Clone", (["out"], POINTER(POINTER(IEnumString)), "ppEnum")),
]
################################################################
## code template for IEnumString implementation
##class IEnumString_Impl(object):
##    def RemoteNext(self, celt):
##        '-no docstring-'
##        #return rgelt, pceltFetched
##
##    def Skip(self, celt):
##        '-no docstring-'
##        #return
##
##    def Reset(self):
##        '-no docstring-'
##        #return
##
##    def Clone(self):
##        '-no docstring-'
##        #return ppEnum
##


# values for enumeration 'DISPID_SpeechRecoResult2'
DISPID_SRRSetTextFeedback = 12
DISPID_SpeechRecoResult2 = c_int  # enum
SPEVENTSOURCEINFO._fields_ = [
    ("ullEventInterest", c_ulonglong),
    ("ullQueuedInterest", c_ulonglong),
    ("ulCount", c_ulong),
]
assert sizeof(SPEVENTSOURCEINFO) == 24, sizeof(SPEVENTSOURCEINFO)
assert alignment(SPEVENTSOURCEINFO) == 8, alignment(SPEVENTSOURCEINFO)
ISpMMSysAudio._methods_ = [
    COMMETHOD([], HRESULT, "GetDeviceId", (["out"], POINTER(c_uint), "puDeviceId")),
    COMMETHOD([], HRESULT, "SetDeviceId", (["in"], c_uint, "uDeviceId")),
    COMMETHOD([], HRESULT, "GetMMHandle", (["out"], POINTER(c_void_p), "pHandle")),
    COMMETHOD([], HRESULT, "GetLineId", (["out"], POINTER(c_uint), "puLineId")),
    COMMETHOD([], HRESULT, "SetLineId", (["in"], c_uint, "uLineId")),
]
################################################################
## code template for ISpMMSysAudio implementation
##class ISpMMSysAudio_Impl(object):
##    def GetDeviceId(self):
##        '-no docstring-'
##        #return puDeviceId
##
##    def SetDeviceId(self, uDeviceId):
##        '-no docstring-'
##        #return
##
##    def GetMMHandle(self):
##        '-no docstring-'
##        #return pHandle
##
##    def GetLineId(self):
##        '-no docstring-'
##        #return puLineId
##
##    def SetLineId(self, uLineId):
##        '-no docstring-'
##        #return
##


# values for enumeration 'SpeechGrammarRuleStateTransitionType'
SGRSTTEpsilon = 0
SGRSTTWord = 1
SGRSTTRule = 2
SGRSTTDictation = 3
SGRSTTWildcard = 4
SGRSTTTextBuffer = 5
SpeechGrammarRuleStateTransitionType = c_int  # enum
ISpeechGrammarRuleStateTransition._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Type"), "propget"],
        HRESULT,
        "Type",
        (["out", "retval"], POINTER(SpeechGrammarRuleStateTransitionType), "Type"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Text"), "propget"],
        HRESULT,
        "Text",
        (["out", "retval"], POINTER(BSTR), "Text"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Rule"), "propget"],
        HRESULT,
        "Rule",
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRule)), "Rule"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Weight"), "propget"],
        HRESULT,
        "Weight",
        (["out", "retval"], POINTER(VARIANT), "Weight"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("PropertyName"), "propget"],
        HRESULT,
        "PropertyName",
        (["out", "retval"], POINTER(BSTR), "PropertyName"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("PropertyId"), "propget"],
        HRESULT,
        "PropertyId",
        (["out", "retval"], POINTER(c_int), "PropertyId"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("PropertyValue"), "propget"],
        HRESULT,
        "PropertyValue",
        (["out", "retval"], POINTER(VARIANT), "PropertyValue"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("NextState"), "propget"],
        HRESULT,
        "NextState",
        (["out", "retval"], POINTER(POINTER(ISpeechGrammarRuleState)), "NextState"),
    ),
]
################################################################
## code template for ISpeechGrammarRuleStateTransition implementation
##class ISpeechGrammarRuleStateTransition_Impl(object):
##    @property
##    def Type(self):
##        'Type'
##        #return Type
##
##    @property
##    def Text(self):
##        'Text'
##        #return Text
##
##    @property
##    def Rule(self):
##        'Rule'
##        #return Rule
##
##    @property
##    def Weight(self):
##        'Weight'
##        #return Weight
##
##    @property
##    def PropertyName(self):
##        'PropertyName'
##        #return PropertyName
##
##    @property
##    def PropertyId(self):
##        'PropertyId'
##        #return PropertyId
##
##    @property
##    def PropertyValue(self):
##        'PropertyValue'
##        #return PropertyValue
##
##    @property
##    def NextState(self):
##        'NextState'
##        #return NextState
##


# values for enumeration 'SpeechVisemeFeature'
SVF_None = 0
SVF_Stressed = 1
SVF_Emphasis = 2
SpeechVisemeFeature = c_int  # enum

# values for enumeration 'SpeechVisemeType'
SVP_0 = 0
SVP_1 = 1
SVP_2 = 2
SVP_3 = 3
SVP_4 = 4
SVP_5 = 5
SVP_6 = 6
SVP_7 = 7
SVP_8 = 8
SVP_9 = 9
SVP_10 = 10
SVP_11 = 11
SVP_12 = 12
SVP_13 = 13
SVP_14 = 14
SVP_15 = 15
SVP_16 = 16
SVP_17 = 17
SVP_18 = 18
SVP_19 = 19
SVP_20 = 20
SVP_21 = 21
SpeechVisemeType = c_int  # enum
_ISpeechVoiceEvents._disp_methods_ = [
    DISPMETHOD(
        [dispid(1), helpstring("StartStream")],
        None,
        "StartStream",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(2), helpstring("EndStream")],
        None,
        "EndStream",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
    ),
    DISPMETHOD(
        [dispid(3), helpstring("VoiceChange")],
        None,
        "VoiceChange",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], POINTER(ISpeechObjectToken), "VoiceObjectToken"),
    ),
    DISPMETHOD(
        [dispid(4), helpstring("Bookmark")],
        None,
        "Bookmark",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], BSTR, "Bookmark"),
        (["in"], c_int, "BookmarkId"),
    ),
    DISPMETHOD(
        [dispid(5), helpstring("Word")],
        None,
        "Word",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], c_int, "CharacterPosition"),
        (["in"], c_int, "Length"),
    ),
    DISPMETHOD(
        [dispid(7), helpstring("Sentence")],
        None,
        "Sentence",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], c_int, "CharacterPosition"),
        (["in"], c_int, "Length"),
    ),
    DISPMETHOD(
        [dispid(6), helpstring("Phoneme")],
        None,
        "Phoneme",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], c_int, "Duration"),
        (["in"], c_short, "NextPhoneId"),
        (["in"], SpeechVisemeFeature, "Feature"),
        (["in"], c_short, "CurrentPhoneId"),
    ),
    DISPMETHOD(
        [dispid(8), helpstring("Viseme")],
        None,
        "Viseme",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], c_int, "Duration"),
        (["in"], SpeechVisemeType, "NextVisemeId"),
        (["in"], SpeechVisemeFeature, "Feature"),
        (["in"], SpeechVisemeType, "CurrentVisemeId"),
    ),
    DISPMETHOD(
        [dispid(9), helpstring("AudioLevel")],
        None,
        "AudioLevel",
        (["in"], c_int, "StreamNumber"),
        (["in"], VARIANT, "StreamPosition"),
        (["in"], c_int, "AudioLevel"),
    ),
    DISPMETHOD(
        [dispid(10), helpstring("EnginePrivate")],
        None,
        "EnginePrivate",
        (["in"], c_int, "StreamNumber"),
        (["in"], c_int, "StreamPosition"),
        (["in"], VARIANT, "EngineData"),
    ),
]


class ISpeechRecoResult2(ISpeechRecoResult):
    _case_insensitive_ = True
    "ISpeechRecoResult2 Interface"
    _iid_ = GUID("{8E0A246D-D3C8-45DE-8657-04290C458C3C}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechRecoResult2._methods_ = [
    COMMETHOD(
        [dispid(12), helpstring("DiscardResultInfo")],
        HRESULT,
        "SetTextFeedback",
        (["in"], BSTR, "Feedback"),
        (["in"], VARIANT_BOOL, "WasSuccessful"),
    ),
]
################################################################
## code template for ISpeechRecoResult2 implementation
##class ISpeechRecoResult2_Impl(object):
##    def SetTextFeedback(self, Feedback, WasSuccessful):
##        'DiscardResultInfo'
##        #return
##

ISpeechPhraseElement._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("AudioTimeOffset"), "propget"],
        HRESULT,
        "AudioTimeOffset",
        (["out", "retval"], POINTER(c_int), "AudioTimeOffset"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("AudioSizeTime"), "propget"],
        HRESULT,
        "AudioSizeTime",
        (["out", "retval"], POINTER(c_int), "AudioSizeTime"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AudioStreamOffset"), "propget"],
        HRESULT,
        "AudioStreamOffset",
        (["out", "retval"], POINTER(c_int), "AudioStreamOffset"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AudioSizeBytes"), "propget"],
        HRESULT,
        "AudioSizeBytes",
        (["out", "retval"], POINTER(c_int), "AudioSizeBytes"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("RetainedStreamOffset"), "propget"],
        HRESULT,
        "RetainedStreamOffset",
        (["out", "retval"], POINTER(c_int), "RetainedStreamOffset"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("RetainedSizeBytes"), "propget"],
        HRESULT,
        "RetainedSizeBytes",
        (["out", "retval"], POINTER(c_int), "RetainedSizeBytes"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("DisplayText"), "propget"],
        HRESULT,
        "DisplayText",
        (["out", "retval"], POINTER(BSTR), "DisplayText"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("LexicalForm"), "propget"],
        HRESULT,
        "LexicalForm",
        (["out", "retval"], POINTER(BSTR), "LexicalForm"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("Pronunciation"), "propget"],
        HRESULT,
        "Pronunciation",
        (["out", "retval"], POINTER(VARIANT), "Pronunciation"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("DisplayAttributes"), "propget"],
        HRESULT,
        "DisplayAttributes",
        (["out", "retval"], POINTER(SpeechDisplayAttributes), "DisplayAttributes"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("RequiredConfidence"), "propget"],
        HRESULT,
        "RequiredConfidence",
        (["out", "retval"], POINTER(SpeechEngineConfidence), "RequiredConfidence"),
    ),
    COMMETHOD(
        [dispid(12), helpstring("ActualConfidence"), "propget"],
        HRESULT,
        "ActualConfidence",
        (["out", "retval"], POINTER(SpeechEngineConfidence), "ActualConfidence"),
    ),
    COMMETHOD(
        [dispid(13), helpstring("EngineConfidence"), "propget"],
        HRESULT,
        "EngineConfidence",
        (["out", "retval"], POINTER(c_float), "EngineConfidence"),
    ),
]
################################################################
## code template for ISpeechPhraseElement implementation
##class ISpeechPhraseElement_Impl(object):
##    @property
##    def AudioTimeOffset(self):
##        'AudioTimeOffset'
##        #return AudioTimeOffset
##
##    @property
##    def AudioSizeTime(self):
##        'AudioSizeTime'
##        #return AudioSizeTime
##
##    @property
##    def AudioStreamOffset(self):
##        'AudioStreamOffset'
##        #return AudioStreamOffset
##
##    @property
##    def AudioSizeBytes(self):
##        'AudioSizeBytes'
##        #return AudioSizeBytes
##
##    @property
##    def RetainedStreamOffset(self):
##        'RetainedStreamOffset'
##        #return RetainedStreamOffset
##
##    @property
##    def RetainedSizeBytes(self):
##        'RetainedSizeBytes'
##        #return RetainedSizeBytes
##
##    @property
##    def DisplayText(self):
##        'DisplayText'
##        #return DisplayText
##
##    @property
##    def LexicalForm(self):
##        'LexicalForm'
##        #return LexicalForm
##
##    @property
##    def Pronunciation(self):
##        'Pronunciation'
##        #return Pronunciation
##
##    @property
##    def DisplayAttributes(self):
##        'DisplayAttributes'
##        #return DisplayAttributes
##
##    @property
##    def RequiredConfidence(self):
##        'RequiredConfidence'
##        #return RequiredConfidence
##
##    @property
##    def ActualConfidence(self):
##        'ActualConfidence'
##        #return ActualConfidence
##
##    @property
##    def EngineConfidence(self):
##        'EngineConfidence'
##        #return EngineConfidence
##

ISpPhoneticAlphabetSelection._methods_ = [
    COMMETHOD([], HRESULT, "IsAlphabetUPS", (["out"], POINTER(c_int), "pfIsUPS")),
    COMMETHOD([], HRESULT, "SetAlphabetToUPS", (["in"], c_int, "fForceUPS")),
]
################################################################
## code template for ISpPhoneticAlphabetSelection implementation
##class ISpPhoneticAlphabetSelection_Impl(object):
##    def IsAlphabetUPS(self):
##        '-no docstring-'
##        #return pfIsUPS
##
##    def SetAlphabetToUPS(self, fForceUPS):
##        '-no docstring-'
##        #return
##


# values for enumeration 'SpeechStreamSeekPositionType'
SSSPTRelativeToStart = 0
SSSPTRelativeToCurrentPosition = 1
SSSPTRelativeToEnd = 2
SpeechStreamSeekPositionType = c_int  # enum
ISpeechBaseStream._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Format"), "propget"],
        HRESULT,
        "Format",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioFormat)), "AudioFormat"),
    ),
    COMMETHOD(
        [dispid(1), helpstring("Format"), "propputref"],
        HRESULT,
        "Format",
        (["in"], POINTER(ISpeechAudioFormat), "AudioFormat"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Read")],
        HRESULT,
        "Read",
        (["out"], POINTER(VARIANT), "Buffer"),
        (["in"], c_int, "NumberOfBytes"),
        (["out", "retval"], POINTER(c_int), "BytesRead"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("Write")],
        HRESULT,
        "Write",
        (["in"], VARIANT, "Buffer"),
        (["out", "retval"], POINTER(c_int), "BytesWritten"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Seek")],
        HRESULT,
        "Seek",
        (["in"], VARIANT, "Position"),
        (["in", "optional"], SpeechStreamSeekPositionType, "Origin", 0),
        (["out", "retval"], POINTER(VARIANT), "NewPosition"),
    ),
]
################################################################
## code template for ISpeechBaseStream implementation
##class ISpeechBaseStream_Impl(object):
##    def Format(self, AudioFormat):
##        'Format'
##        #return
##
##    def Read(self, NumberOfBytes):
##        'Read'
##        #return Buffer, BytesRead
##
##    def Write(self, Buffer):
##        'Write'
##        #return BytesWritten
##
##    def Seek(self, Position, Origin):
##        'Seek'
##        #return NewPosition
##


class ISpeechFileStream(ISpeechBaseStream):
    _case_insensitive_ = True
    "ISpeechFileStream Interface"
    _iid_ = GUID("{AF67F125-AB39-4E93-B4A2-CC2E66E182A7}")
    _idlflags_ = ["dual", "oleautomation"]


# values for enumeration 'SpeechStreamFileMode'
SSFMOpenForRead = 0
SSFMOpenReadWrite = 1
SSFMCreate = 2
SSFMCreateForWrite = 3
SpeechStreamFileMode = c_int  # enum
ISpeechFileStream._methods_ = [
    COMMETHOD(
        [dispid(100), helpstring("Open")],
        HRESULT,
        "Open",
        (["in"], BSTR, "FileName"),
        (["in", "optional"], SpeechStreamFileMode, "FileMode", 0),
        (["in", "optional"], VARIANT_BOOL, "DoEvents", False),
    ),
    COMMETHOD([dispid(101), helpstring("Close")], HRESULT, "Close"),
]
################################################################
## code template for ISpeechFileStream implementation
##class ISpeechFileStream_Impl(object):
##    def Open(self, FileName, FileMode, DoEvents):
##        'Open'
##        #return
##
##    def Close(self):
##        'Close'
##        #return
##


class ISpeechCustomStream(ISpeechBaseStream):
    _case_insensitive_ = True
    "ISpeechCustomStream Interface"
    _iid_ = GUID("{1A9E9F4F-104F-4DB8-A115-EFD7FD0C97AE}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechCustomStream._methods_ = [
    COMMETHOD(
        [dispid(100), helpstring("BaseStream"), "propget"],
        HRESULT,
        "BaseStream",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "ppUnkStream"),
    ),
    COMMETHOD(
        [dispid(100), helpstring("BaseStream"), "propputref"],
        HRESULT,
        "BaseStream",
        (["in"], POINTER(IUnknown), "ppUnkStream"),
    ),
]
################################################################
## code template for ISpeechCustomStream implementation
##class ISpeechCustomStream_Impl(object):
##    def BaseStream(self, ppUnkStream):
##        'BaseStream'
##        #return
##


class ISpeechAudioBufferInfo(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechAudioBufferInfo Interface"
    _iid_ = GUID("{11B103D8-1142-4EDF-A093-82FB3915F8CC}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechAudio._methods_ = [
    COMMETHOD(
        [dispid(200), helpstring("Status"), "propget"],
        HRESULT,
        "Status",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioStatus)), "Status"),
    ),
    COMMETHOD(
        [dispid(201), helpstring("BufferInfo"), "propget"],
        HRESULT,
        "BufferInfo",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioBufferInfo)), "BufferInfo"),
    ),
    COMMETHOD(
        [dispid(202), helpstring("DefaultFormat"), "propget"],
        HRESULT,
        "DefaultFormat",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioFormat)), "StreamFormat"),
    ),
    COMMETHOD(
        [dispid(203), helpstring("Volume"), "propget"],
        HRESULT,
        "Volume",
        (["out", "retval"], POINTER(c_int), "Volume"),
    ),
    COMMETHOD(
        [dispid(203), helpstring("Volume"), "propput"],
        HRESULT,
        "Volume",
        (["in"], c_int, "Volume"),
    ),
    COMMETHOD(
        [dispid(204), helpstring("BufferNotifySize"), "propget"],
        HRESULT,
        "BufferNotifySize",
        (["out", "retval"], POINTER(c_int), "BufferNotifySize"),
    ),
    COMMETHOD(
        [dispid(204), helpstring("BufferNotifySize"), "propput"],
        HRESULT,
        "BufferNotifySize",
        (["in"], c_int, "BufferNotifySize"),
    ),
    COMMETHOD(
        [dispid(205), helpstring("EventHandle"), "hidden", "propget"],
        HRESULT,
        "EventHandle",
        (["out", "retval"], POINTER(c_int), "EventHandle"),
    ),
    COMMETHOD(
        [dispid(206), helpstring("SetState"), "hidden"],
        HRESULT,
        "SetState",
        (["in"], SpeechAudioState, "State"),
    ),
]
################################################################
## code template for ISpeechAudio implementation
##class ISpeechAudio_Impl(object):
##    @property
##    def Status(self):
##        'Status'
##        #return Status
##
##    @property
##    def BufferInfo(self):
##        'BufferInfo'
##        #return BufferInfo
##
##    @property
##    def DefaultFormat(self):
##        'DefaultFormat'
##        #return StreamFormat
##
##    def _get(self):
##        'Volume'
##        #return Volume
##    def _set(self, Volume):
##        'Volume'
##    Volume = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'BufferNotifySize'
##        #return BufferNotifySize
##    def _set(self, BufferNotifySize):
##        'BufferNotifySize'
##    BufferNotifySize = property(_get, _set, doc = _set.__doc__)
##
##    @property
##    def EventHandle(self):
##        'EventHandle'
##        #return EventHandle
##
##    def SetState(self, State):
##        'SetState'
##        #return
##

ISpeechAudioBufferInfo._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("MinNotification"), "propget"],
        HRESULT,
        "MinNotification",
        (["out", "retval"], POINTER(c_int), "MinNotification"),
    ),
    COMMETHOD(
        [dispid(1), helpstring("MinNotification"), "propput"],
        HRESULT,
        "MinNotification",
        (["in"], c_int, "MinNotification"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("BufferSize"), "propget"],
        HRESULT,
        "BufferSize",
        (["out", "retval"], POINTER(c_int), "BufferSize"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("BufferSize"), "propput"],
        HRESULT,
        "BufferSize",
        (["in"], c_int, "BufferSize"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("EventBias"), "propget"],
        HRESULT,
        "EventBias",
        (["out", "retval"], POINTER(c_int), "EventBias"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("EventBias"), "propput"],
        HRESULT,
        "EventBias",
        (["in"], c_int, "EventBias"),
    ),
]
################################################################
## code template for ISpeechAudioBufferInfo implementation
##class ISpeechAudioBufferInfo_Impl(object):
##    def _get(self):
##        'MinNotification'
##        #return MinNotification
##    def _set(self, MinNotification):
##        'MinNotification'
##    MinNotification = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'BufferSize'
##        #return BufferSize
##    def _set(self, BufferSize):
##        'BufferSize'
##    BufferSize = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'EventBias'
##        #return EventBias
##    def _set(self, EventBias):
##        'EventBias'
##    EventBias = property(_get, _set, doc = _set.__doc__)
##

ISpRecoContext._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetRecognizer",
        (["out"], POINTER(POINTER(ISpRecognizer)), "ppRecognizer"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "CreateGrammar",
        (["in"], c_ulonglong, "ullGrammarID"),
        (["out"], POINTER(POINTER(ISpRecoGrammar)), "ppGrammar"),
    ),
    COMMETHOD(
        [], HRESULT, "GetStatus", (["out"], POINTER(SPRECOCONTEXTSTATUS), "pStatus")
    ),
    COMMETHOD(
        [], HRESULT, "GetMaxAlternates", (["in"], POINTER(c_ulong), "pcAlternates")
    ),
    COMMETHOD([], HRESULT, "SetMaxAlternates", (["in"], c_ulong, "cAlternates")),
    COMMETHOD(
        [],
        HRESULT,
        "SetAudioOptions",
        (["in"], SPAUDIOOPTIONS, "Options"),
        (
            ["in"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pAudioFormatId",
        ),
        (["in"], POINTER(WAVEFORMATEX), "pWaveFormatEx"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetAudioOptions",
        (["in"], POINTER(SPAUDIOOPTIONS), "pOptions"),
        (
            ["out"],
            POINTER(comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
            "pAudioFormatId",
        ),
        (["out"], POINTER(POINTER(WAVEFORMATEX)), "ppCoMemWFEX"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "DeserializeResult",
        (["in"], POINTER(SPSERIALIZEDRESULT), "pSerializedResult"),
        (["out"], POINTER(POINTER(ISpRecoResult)), "ppResult"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "Bookmark",
        (["in"], SPBOOKMARKOPTIONS, "Options"),
        (["in"], c_ulonglong, "ullStreamPosition"),
        (["in"], LONG_PTR, "lparamEvent"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetAdaptationData",
        (["in"], WSTRING, "pAdaptationData"),
        (["in"], c_ulong, "cch"),
    ),
    COMMETHOD([], HRESULT, "Pause", (["in"], c_ulong, "dwReserved")),
    COMMETHOD([], HRESULT, "Resume", (["in"], c_ulong, "dwReserved")),
    COMMETHOD(
        [],
        HRESULT,
        "SetVoice",
        (["in"], POINTER(ISpVoice), "pVoice"),
        (["in"], c_int, "fAllowFormatChanges"),
    ),
    COMMETHOD(
        [], HRESULT, "GetVoice", (["out"], POINTER(POINTER(ISpVoice)), "ppVoice")
    ),
    COMMETHOD(
        [], HRESULT, "SetVoicePurgeEvent", (["in"], c_ulonglong, "ullEventInterest")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetVoicePurgeEvent",
        (["out"], POINTER(c_ulonglong), "pullEventInterest"),
    ),
    COMMETHOD(
        [], HRESULT, "SetContextState", (["in"], SPCONTEXTSTATE, "eContextState")
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetContextState",
        (["out"], POINTER(SPCONTEXTSTATE), "peContextState"),
    ),
]
################################################################
## code template for ISpRecoContext implementation
##class ISpRecoContext_Impl(object):
##    def GetRecognizer(self):
##        '-no docstring-'
##        #return ppRecognizer
##
##    def CreateGrammar(self, ullGrammarID):
##        '-no docstring-'
##        #return ppGrammar
##
##    def GetStatus(self):
##        '-no docstring-'
##        #return pStatus
##
##    def GetMaxAlternates(self, pcAlternates):
##        '-no docstring-'
##        #return
##
##    def SetMaxAlternates(self, cAlternates):
##        '-no docstring-'
##        #return
##
##    def SetAudioOptions(self, Options, pAudioFormatId, pWaveFormatEx):
##        '-no docstring-'
##        #return
##
##    def GetAudioOptions(self, pOptions):
##        '-no docstring-'
##        #return pAudioFormatId, ppCoMemWFEX
##
##    def DeserializeResult(self, pSerializedResult):
##        '-no docstring-'
##        #return ppResult
##
##    def Bookmark(self, Options, ullStreamPosition, lparamEvent):
##        '-no docstring-'
##        #return
##
##    def SetAdaptationData(self, pAdaptationData, cch):
##        '-no docstring-'
##        #return
##
##    def Pause(self, dwReserved):
##        '-no docstring-'
##        #return
##
##    def Resume(self, dwReserved):
##        '-no docstring-'
##        #return
##
##    def SetVoice(self, pVoice, fAllowFormatChanges):
##        '-no docstring-'
##        #return
##
##    def GetVoice(self):
##        '-no docstring-'
##        #return ppVoice
##
##    def SetVoicePurgeEvent(self, ullEventInterest):
##        '-no docstring-'
##        #return
##
##    def GetVoicePurgeEvent(self):
##        '-no docstring-'
##        #return pullEventInterest
##
##    def SetContextState(self, eContextState):
##        '-no docstring-'
##        #return
##
##    def GetContextState(self):
##        '-no docstring-'
##        #return peContextState
##


class SPSHORTCUTPAIR(Structure):
    pass


SPSHORTCUTPAIRLIST._fields_ = [
    ("ulSize", c_ulong),
    ("pvBuffer", POINTER(c_ubyte)),
    ("pFirstShortcutPair", POINTER(SPSHORTCUTPAIR)),
]
assert sizeof(SPSHORTCUTPAIRLIST) == 12, sizeof(SPSHORTCUTPAIRLIST)
assert alignment(SPSHORTCUTPAIRLIST) == 4, alignment(SPSHORTCUTPAIRLIST)


class SpPhoneConverter(CoClass):
    "SpPhoneConverter Class"
    _reg_clsid_ = GUID("{9185F743-1143-4C28-86B5-BFF14F20E5C8}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpPhoneConverter(ISpObjectWithToken):
    _case_insensitive_ = True
    "ISpPhoneConverter Interface"
    _iid_ = GUID("{8445C581-0CAC-4A38-ABFE-9B2CE2826455}")
    _idlflags_ = ["restricted"]


SpPhoneConverter._com_interfaces_ = [
    ISpeechPhoneConverter,
    ISpPhoneConverter,
    ISpPhoneticAlphabetSelection,
]

SPSHORTCUTPAIR._fields_ = [
    ("pNextSHORTCUTPAIR", POINTER(SPSHORTCUTPAIR)),
    ("LangId", c_ushort),
    ("shType", SPSHORTCUTTYPE),
    ("pszDisplay", WSTRING),
    ("pszSpoken", WSTRING),
]
assert sizeof(SPSHORTCUTPAIR) == 20, sizeof(SPSHORTCUTPAIR)
assert alignment(SPSHORTCUTPAIR) == 4, alignment(SPSHORTCUTPAIR)
ISpeechMMSysAudio._methods_ = [
    COMMETHOD(
        [dispid(300), helpstring("DeviceId"), "propget"],
        HRESULT,
        "DeviceId",
        (["out", "retval"], POINTER(c_int), "DeviceId"),
    ),
    COMMETHOD(
        [dispid(300), helpstring("DeviceId"), "propput"],
        HRESULT,
        "DeviceId",
        (["in"], c_int, "DeviceId"),
    ),
    COMMETHOD(
        [dispid(301), helpstring("LineId"), "propget"],
        HRESULT,
        "LineId",
        (["out", "retval"], POINTER(c_int), "LineId"),
    ),
    COMMETHOD(
        [dispid(301), helpstring("LineId"), "propput"],
        HRESULT,
        "LineId",
        (["in"], c_int, "LineId"),
    ),
    COMMETHOD(
        [dispid(302), helpstring("MMHandle"), "hidden", "propget"],
        HRESULT,
        "MMHandle",
        (["out", "retval"], POINTER(c_int), "Handle"),
    ),
]
################################################################
## code template for ISpeechMMSysAudio implementation
##class ISpeechMMSysAudio_Impl(object):
##    def _get(self):
##        'DeviceId'
##        #return DeviceId
##    def _set(self, DeviceId):
##        'DeviceId'
##    DeviceId = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'LineId'
##        #return LineId
##    def _set(self, LineId):
##        'LineId'
##    LineId = property(_get, _set, doc = _set.__doc__)
##
##    @property
##    def MMHandle(self):
##        'MMHandle'
##        #return Handle
##


class ISpeechRecognizerStatus(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechRecognizerStatus Interface"
    _iid_ = GUID("{BFF9E781-53EC-484E-BB8A-0E1B5551E35C}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechRecognizer._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Recognizer"), "propputref"],
        HRESULT,
        "Recognizer",
        (["in"], POINTER(ISpeechObjectToken), "Recognizer"),
    ),
    COMMETHOD(
        [dispid(1), helpstring("Recognizer"), "propget"],
        HRESULT,
        "Recognizer",
        (["out", "retval"], POINTER(POINTER(ISpeechObjectToken)), "Recognizer"),
    ),
    COMMETHOD(
        [
            dispid(2),
            helpstring("AllowAudioInputFormatChangesOnNextSet"),
            "hidden",
            "propput",
        ],
        HRESULT,
        "AllowAudioInputFormatChangesOnNextSet",
        (["in"], VARIANT_BOOL, "Allow"),
    ),
    COMMETHOD(
        [
            dispid(2),
            helpstring("AllowAudioInputFormatChangesOnNextSet"),
            "hidden",
            "propget",
        ],
        HRESULT,
        "AllowAudioInputFormatChangesOnNextSet",
        (["out", "retval"], POINTER(VARIANT_BOOL), "Allow"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AudioInput"), "propputref"],
        HRESULT,
        "AudioInput",
        (["in", "optional"], POINTER(ISpeechObjectToken), "AudioInput", 0),
    ),
    COMMETHOD(
        [dispid(3), helpstring("AudioInput"), "propget"],
        HRESULT,
        "AudioInput",
        (["out", "retval"], POINTER(POINTER(ISpeechObjectToken)), "AudioInput"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AudioInputStream"), "propputref"],
        HRESULT,
        "AudioInputStream",
        (["in", "optional"], POINTER(ISpeechBaseStream), "AudioInputStream", 0),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AudioInputStream"), "propget"],
        HRESULT,
        "AudioInputStream",
        (["out", "retval"], POINTER(POINTER(ISpeechBaseStream)), "AudioInputStream"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("IsShared"), "propget"],
        HRESULT,
        "IsShared",
        (["out", "retval"], POINTER(VARIANT_BOOL), "Shared"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("State"), "propput"],
        HRESULT,
        "State",
        (["in"], SpeechRecognizerState, "State"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("State"), "propget"],
        HRESULT,
        "State",
        (["out", "retval"], POINTER(SpeechRecognizerState), "State"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("Status"), "propget"],
        HRESULT,
        "Status",
        (["out", "retval"], POINTER(POINTER(ISpeechRecognizerStatus)), "Status"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("Profile"), "propputref"],
        HRESULT,
        "Profile",
        (["in", "optional"], POINTER(ISpeechObjectToken), "Profile", 0),
    ),
    COMMETHOD(
        [dispid(8), helpstring("Profile"), "propget"],
        HRESULT,
        "Profile",
        (["out", "retval"], POINTER(POINTER(ISpeechObjectToken)), "Profile"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("EmulateRecognition")],
        HRESULT,
        "EmulateRecognition",
        (["in"], VARIANT, "TextElements"),
        (["in", "optional"], POINTER(VARIANT), "ElementDisplayAttributes"),
        (["in", "optional"], c_int, "LanguageId", 0),
    ),
    COMMETHOD(
        [dispid(10), helpstring("CreateRecoContext")],
        HRESULT,
        "CreateRecoContext",
        (["out", "retval"], POINTER(POINTER(ISpeechRecoContext)), "NewContext"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("GetFormat")],
        HRESULT,
        "GetFormat",
        (["in"], SpeechFormatType, "Type"),
        (["out", "retval"], POINTER(POINTER(ISpeechAudioFormat)), "Format"),
    ),
    COMMETHOD(
        [dispid(12), helpstring("SetPropertyNumber"), "hidden"],
        HRESULT,
        "SetPropertyNumber",
        (["in"], BSTR, "Name"),
        (["in"], c_int, "Value"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Supported"),
    ),
    COMMETHOD(
        [dispid(13), helpstring("GetPropertyNumber"), "hidden"],
        HRESULT,
        "GetPropertyNumber",
        (["in"], BSTR, "Name"),
        (["in", "out"], POINTER(c_int), "Value"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Supported"),
    ),
    COMMETHOD(
        [dispid(14), helpstring("SetPropertyString"), "hidden"],
        HRESULT,
        "SetPropertyString",
        (["in"], BSTR, "Name"),
        (["in"], BSTR, "Value"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Supported"),
    ),
    COMMETHOD(
        [dispid(15), helpstring("GetPropertyString"), "hidden"],
        HRESULT,
        "GetPropertyString",
        (["in"], BSTR, "Name"),
        (["in", "out"], POINTER(BSTR), "Value"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Supported"),
    ),
    COMMETHOD(
        [dispid(16), helpstring("IsUISupported")],
        HRESULT,
        "IsUISupported",
        (["in"], BSTR, "TypeOfUI"),
        (["in", "optional"], POINTER(VARIANT), "ExtraData"),
        (["out", "retval"], POINTER(VARIANT_BOOL), "Supported"),
    ),
    COMMETHOD(
        [dispid(17), helpstring("DisplayUI")],
        HRESULT,
        "DisplayUI",
        (["in"], c_int, "hWndParent"),
        (["in"], BSTR, "Title"),
        (["in"], BSTR, "TypeOfUI"),
        (["in", "optional"], POINTER(VARIANT), "ExtraData"),
    ),
    COMMETHOD(
        [dispid(18), helpstring("GetRecognizers")],
        HRESULT,
        "GetRecognizers",
        (["in", "optional"], BSTR, "RequiredAttributes", ""),
        (["in", "optional"], BSTR, "OptionalAttributes", ""),
        (["out", "retval"], POINTER(POINTER(ISpeechObjectTokens)), "ObjectTokens"),
    ),
    COMMETHOD(
        [dispid(19), helpstring("GetAudioInputs")],
        HRESULT,
        "GetAudioInputs",
        (["in", "optional"], BSTR, "RequiredAttributes", ""),
        (["in", "optional"], BSTR, "OptionalAttributes", ""),
        (["out", "retval"], POINTER(POINTER(ISpeechObjectTokens)), "ObjectTokens"),
    ),
    COMMETHOD(
        [dispid(20), helpstring("GetProfiles")],
        HRESULT,
        "GetProfiles",
        (["in", "optional"], BSTR, "RequiredAttributes", ""),
        (["in", "optional"], BSTR, "OptionalAttributes", ""),
        (["out", "retval"], POINTER(POINTER(ISpeechObjectTokens)), "ObjectTokens"),
    ),
]
################################################################
## code template for ISpeechRecognizer implementation
##class ISpeechRecognizer_Impl(object):
##    @property
##    def Recognizer(self, Recognizer):
##        'Recognizer'
##        #return
##
##    def _get(self):
##        'AllowAudioInputFormatChangesOnNextSet'
##        #return Allow
##    def _set(self, Allow):
##        'AllowAudioInputFormatChangesOnNextSet'
##    AllowAudioInputFormatChangesOnNextSet = property(_get, _set, doc = _set.__doc__)
##
##    @property
##    def AudioInput(self, AudioInput):
##        'AudioInput'
##        #return
##
##    @property
##    def AudioInputStream(self, AudioInputStream):
##        'AudioInputStream'
##        #return
##
##    @property
##    def IsShared(self):
##        'IsShared'
##        #return Shared
##
##    def _get(self):
##        'State'
##        #return State
##    def _set(self, State):
##        'State'
##    State = property(_get, _set, doc = _set.__doc__)
##
##    @property
##    def Status(self):
##        'Status'
##        #return Status
##
##    @property
##    def Profile(self, Profile):
##        'Profile'
##        #return
##
##    def EmulateRecognition(self, TextElements, ElementDisplayAttributes, LanguageId):
##        'EmulateRecognition'
##        #return
##
##    def CreateRecoContext(self):
##        'CreateRecoContext'
##        #return NewContext
##
##    def GetFormat(self, Type):
##        'GetFormat'
##        #return Format
##
##    def SetPropertyNumber(self, Name, Value):
##        'SetPropertyNumber'
##        #return Supported
##
##    def GetPropertyNumber(self, Name):
##        'GetPropertyNumber'
##        #return Value, Supported
##
##    def SetPropertyString(self, Name, Value):
##        'SetPropertyString'
##        #return Supported
##
##    def GetPropertyString(self, Name):
##        'GetPropertyString'
##        #return Value, Supported
##
##    def IsUISupported(self, TypeOfUI, ExtraData):
##        'IsUISupported'
##        #return Supported
##
##    def DisplayUI(self, hWndParent, Title, TypeOfUI, ExtraData):
##        'DisplayUI'
##        #return
##
##    def GetRecognizers(self, RequiredAttributes, OptionalAttributes):
##        'GetRecognizers'
##        #return ObjectTokens
##
##    def GetAudioInputs(self, RequiredAttributes, OptionalAttributes):
##        'GetAudioInputs'
##        #return ObjectTokens
##
##    def GetProfiles(self, RequiredAttributes, OptionalAttributes):
##        'GetProfiles'
##        #return ObjectTokens
##


# values for enumeration 'SpeechDataKeyLocation'
SDKLDefaultLocation = 0
SDKLCurrentUser = 1
SDKLLocalMachine = 2
SDKLCurrentConfig = 5
SpeechDataKeyLocation = c_int  # enum
ISpeechObjectTokenCategory._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Id"), "propget"],
        HRESULT,
        "Id",
        (["out", "retval"], POINTER(BSTR), "Id"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Default"), "propput"],
        HRESULT,
        "Default",
        (["in"], BSTR, "TokenId"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Default"), "propget"],
        HRESULT,
        "Default",
        (["out", "retval"], POINTER(BSTR), "TokenId"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("SetId")],
        HRESULT,
        "SetId",
        (["in"], BSTR, "Id"),
        (["in", "optional"], VARIANT_BOOL, "CreateIfNotExist", False),
    ),
    COMMETHOD(
        [dispid(4), helpstring("GetDataKey"), "hidden"],
        HRESULT,
        "GetDataKey",
        (["in", "optional"], SpeechDataKeyLocation, "Location", 0),
        (["out", "retval"], POINTER(POINTER(ISpeechDataKey)), "DataKey"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("EnumerateTokens")],
        HRESULT,
        "EnumerateTokens",
        (["in", "optional"], BSTR, "RequiredAttributes", ""),
        (["in", "optional"], BSTR, "OptionalAttributes", ""),
        (["out", "retval"], POINTER(POINTER(ISpeechObjectTokens)), "Tokens"),
    ),
]
################################################################
## code template for ISpeechObjectTokenCategory implementation
##class ISpeechObjectTokenCategory_Impl(object):
##    @property
##    def Id(self):
##        'Id'
##        #return Id
##
##    def _get(self):
##        'Default'
##        #return TokenId
##    def _set(self, TokenId):
##        'Default'
##    Default = property(_get, _set, doc = _set.__doc__)
##
##    def SetId(self, Id, CreateIfNotExist):
##        'SetId'
##        #return
##
##    def GetDataKey(self, Location):
##        'GetDataKey'
##        #return DataKey
##
##    def EnumerateTokens(self, RequiredAttributes, OptionalAttributes):
##        'EnumerateTokens'
##        #return Tokens
##

ISpPhoneConverter._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "PhoneToId",
        (["in"], WSTRING, "pszPhone"),
        (["out"], POINTER(c_ushort), "pId"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "IdToPhone",
        (["in"], WSTRING, "pId"),
        (["out"], POINTER(c_ushort), "pszPhone"),
    ),
]
################################################################
## code template for ISpPhoneConverter implementation
##class ISpPhoneConverter_Impl(object):
##    def PhoneToId(self, pszPhone):
##        '-no docstring-'
##        #return pId
##
##    def IdToPhone(self, pId):
##        '-no docstring-'
##        #return pszPhone
##

ISpeechPhraseReplacement._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("DisplayAttributes"), "propget"],
        HRESULT,
        "DisplayAttributes",
        (["out", "retval"], POINTER(SpeechDisplayAttributes), "DisplayAttributes"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Text"), "propget"],
        HRESULT,
        "Text",
        (["out", "retval"], POINTER(BSTR), "Text"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("FirstElement"), "propget"],
        HRESULT,
        "FirstElement",
        (["out", "retval"], POINTER(c_int), "FirstElement"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("NumElements"), "propget"],
        HRESULT,
        "NumberOfElements",
        (["out", "retval"], POINTER(c_int), "NumberOfElements"),
    ),
]
################################################################
## code template for ISpeechPhraseReplacement implementation
##class ISpeechPhraseReplacement_Impl(object):
##    @property
##    def DisplayAttributes(self):
##        'DisplayAttributes'
##        #return DisplayAttributes
##
##    @property
##    def Text(self):
##        'Text'
##        #return Text
##
##    @property
##    def FirstElement(self):
##        'FirstElement'
##        #return FirstElement
##
##    @property
##    def NumberOfElements(self):
##        'NumElements'
##        #return NumberOfElements
##


# values for enumeration 'SpeechRunState'
SRSEDone = 1
SRSEIsSpeaking = 2
SpeechRunState = c_int  # enum
ISpeechVoiceStatus._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("CurrentStreamNumber"), "propget"],
        HRESULT,
        "CurrentStreamNumber",
        (["out", "retval"], POINTER(c_int), "StreamNumber"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("LastStreamNumberQueued"), "propget"],
        HRESULT,
        "LastStreamNumberQueued",
        (["out", "retval"], POINTER(c_int), "StreamNumber"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("LastHResult"), "propget"],
        HRESULT,
        "LastHResult",
        (["out", "retval"], POINTER(c_int), "HResult"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("RunningState"), "propget"],
        HRESULT,
        "RunningState",
        (["out", "retval"], POINTER(SpeechRunState), "State"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("InputWordPosition"), "propget"],
        HRESULT,
        "InputWordPosition",
        (["out", "retval"], POINTER(c_int), "Position"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("InputWordLength"), "propget"],
        HRESULT,
        "InputWordLength",
        (["out", "retval"], POINTER(c_int), "Length"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("InputSentencePosition"), "propget"],
        HRESULT,
        "InputSentencePosition",
        (["out", "retval"], POINTER(c_int), "Position"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("InputSentenceLength"), "propget"],
        HRESULT,
        "InputSentenceLength",
        (["out", "retval"], POINTER(c_int), "Length"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("LastBookmark"), "propget"],
        HRESULT,
        "LastBookmark",
        (["out", "retval"], POINTER(BSTR), "Bookmark"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("LastBookmarkId"), "hidden", "propget"],
        HRESULT,
        "LastBookmarkId",
        (["out", "retval"], POINTER(c_int), "BookmarkId"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("PhonemeId"), "propget"],
        HRESULT,
        "PhonemeId",
        (["out", "retval"], POINTER(c_short), "PhoneId"),
    ),
    COMMETHOD(
        [dispid(12), helpstring("VisemeId"), "propget"],
        HRESULT,
        "VisemeId",
        (["out", "retval"], POINTER(c_short), "VisemeId"),
    ),
]
################################################################
## code template for ISpeechVoiceStatus implementation
##class ISpeechVoiceStatus_Impl(object):
##    @property
##    def CurrentStreamNumber(self):
##        'CurrentStreamNumber'
##        #return StreamNumber
##
##    @property
##    def LastStreamNumberQueued(self):
##        'LastStreamNumberQueued'
##        #return StreamNumber
##
##    @property
##    def LastHResult(self):
##        'LastHResult'
##        #return HResult
##
##    @property
##    def RunningState(self):
##        'RunningState'
##        #return State
##
##    @property
##    def InputWordPosition(self):
##        'InputWordPosition'
##        #return Position
##
##    @property
##    def InputWordLength(self):
##        'InputWordLength'
##        #return Length
##
##    @property
##    def InputSentencePosition(self):
##        'InputSentencePosition'
##        #return Position
##
##    @property
##    def InputSentenceLength(self):
##        'InputSentenceLength'
##        #return Length
##
##    @property
##    def LastBookmark(self):
##        'LastBookmark'
##        #return Bookmark
##
##    @property
##    def LastBookmarkId(self):
##        'LastBookmarkId'
##        #return BookmarkId
##
##    @property
##    def PhonemeId(self):
##        'PhonemeId'
##        #return PhoneId
##
##    @property
##    def VisemeId(self):
##        'VisemeId'
##        #return VisemeId
##

ISpeechMemoryStream._methods_ = [
    COMMETHOD(
        [dispid(100), helpstring("SetData")],
        HRESULT,
        "SetData",
        (["in"], VARIANT, "Data"),
    ),
    COMMETHOD(
        [dispid(101), helpstring("GetData")],
        HRESULT,
        "GetData",
        (["out", "retval"], POINTER(VARIANT), "pData"),
    ),
]
################################################################
## code template for ISpeechMemoryStream implementation
##class ISpeechMemoryStream_Impl(object):
##    def SetData(self, Data):
##        'SetData'
##        #return
##
##    def GetData(self):
##        'GetData'
##        #return pData
##


class SpPhoneticAlphabetConverter(CoClass):
    "SpPhoneticAlphabetConverter Class"
    _reg_clsid_ = GUID("{4F414126-DFE3-4629-99EE-797978317EAD}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


class ISpPhoneticAlphabetConverter(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpPhoneticAlphabetConverter Interface"
    _iid_ = GUID("{133ADCD4-19B4-4020-9FDC-842E78253B17}")
    _idlflags_ = ["restricted"]


SpPhoneticAlphabetConverter._com_interfaces_ = [ISpPhoneticAlphabetConverter]

ISpPhoneticAlphabetConverter._methods_ = [
    COMMETHOD([], HRESULT, "GetLangId", (["out"], POINTER(c_ushort), "pLangID")),
    COMMETHOD([], HRESULT, "SetLangId", (["in"], c_ushort, "LangId")),
    COMMETHOD(
        [],
        HRESULT,
        "SAPI2UPS",
        (["in"], POINTER(c_ushort), "pszSAPIId"),
        (["out"], POINTER(c_ushort), "pszUPSId"),
        (["in"], c_ulong, "cMaxLength"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "UPS2SAPI",
        (["in"], POINTER(c_ushort), "pszUPSId"),
        (["out"], POINTER(c_ushort), "pszSAPIId"),
        (["in"], c_ulong, "cMaxLength"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetMaxConvertLength",
        (["in"], c_ulong, "cSrcLength"),
        (["in"], c_int, "bSAPI2UPS"),
        (["out"], POINTER(c_ulong), "pcMaxDestLength"),
    ),
]
################################################################
## code template for ISpPhoneticAlphabetConverter implementation
##class ISpPhoneticAlphabetConverter_Impl(object):
##    def GetLangId(self):
##        '-no docstring-'
##        #return pLangID
##
##    def SetLangId(self, LangId):
##        '-no docstring-'
##        #return
##
##    def SAPI2UPS(self, pszSAPIId, cMaxLength):
##        '-no docstring-'
##        #return pszUPSId
##
##    def UPS2SAPI(self, pszUPSId, cMaxLength):
##        '-no docstring-'
##        #return pszSAPIId
##
##    def GetMaxConvertLength(self, cSrcLength, bSAPI2UPS):
##        '-no docstring-'
##        #return pcMaxDestLength
##


class SpNullPhoneConverter(CoClass):
    "SpNullPhoneConverter Class"
    _reg_clsid_ = GUID("{455F24E9-7396-4A16-9715-7C0FDBE3EFE3}")
    _idlflags_ = ["hidden", "restricted"]
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpNullPhoneConverter._com_interfaces_ = [ISpPhoneConverter]

ISpeechRecognizerStatus._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("AudioStatus"), "propget"],
        HRESULT,
        "AudioStatus",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioStatus)), "AudioStatus"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("CurrentStreamPosition"), "propget"],
        HRESULT,
        "CurrentStreamPosition",
        (["out", "retval"], POINTER(VARIANT), "pCurrentStreamPos"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("CurrentStreamNumber"), "propget"],
        HRESULT,
        "CurrentStreamNumber",
        (["out", "retval"], POINTER(c_int), "StreamNumber"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("NumberOfActiveRules"), "propget"],
        HRESULT,
        "NumberOfActiveRules",
        (["out", "retval"], POINTER(c_int), "NumberOfActiveRules"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("ClsidEngine"), "propget"],
        HRESULT,
        "ClsidEngine",
        (["out", "retval"], POINTER(BSTR), "ClsidEngine"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("SupportedLanguages"), "propget"],
        HRESULT,
        "SupportedLanguages",
        (["out", "retval"], POINTER(VARIANT), "SupportedLanguages"),
    ),
]
################################################################
## code template for ISpeechRecognizerStatus implementation
##class ISpeechRecognizerStatus_Impl(object):
##    @property
##    def AudioStatus(self):
##        'AudioStatus'
##        #return AudioStatus
##
##    @property
##    def CurrentStreamPosition(self):
##        'CurrentStreamPosition'
##        #return pCurrentStreamPos
##
##    @property
##    def CurrentStreamNumber(self):
##        'CurrentStreamNumber'
##        #return StreamNumber
##
##    @property
##    def NumberOfActiveRules(self):
##        'NumberOfActiveRules'
##        #return NumberOfActiveRules
##
##    @property
##    def ClsidEngine(self):
##        'ClsidEngine'
##        #return ClsidEngine
##
##    @property
##    def SupportedLanguages(self):
##        'SupportedLanguages'
##        #return SupportedLanguages
##


# values for enumeration 'SpeechAudioFormatType'
SAFTDefault = -1
SAFTNoAssignedFormat = 0
SAFTText = 1
SAFTNonStandardFormat = 2
SAFTExtendedAudioFormat = 3
SAFT8kHz8BitMono = 4
SAFT8kHz8BitStereo = 5
SAFT8kHz16BitMono = 6
SAFT8kHz16BitStereo = 7
SAFT11kHz8BitMono = 8
SAFT11kHz8BitStereo = 9
SAFT11kHz16BitMono = 10
SAFT11kHz16BitStereo = 11
SAFT12kHz8BitMono = 12
SAFT12kHz8BitStereo = 13
SAFT12kHz16BitMono = 14
SAFT12kHz16BitStereo = 15
SAFT16kHz8BitMono = 16
SAFT16kHz8BitStereo = 17
SAFT16kHz16BitMono = 18
SAFT16kHz16BitStereo = 19
SAFT22kHz8BitMono = 20
SAFT22kHz8BitStereo = 21
SAFT22kHz16BitMono = 22
SAFT22kHz16BitStereo = 23
SAFT24kHz8BitMono = 24
SAFT24kHz8BitStereo = 25
SAFT24kHz16BitMono = 26
SAFT24kHz16BitStereo = 27
SAFT32kHz8BitMono = 28
SAFT32kHz8BitStereo = 29
SAFT32kHz16BitMono = 30
SAFT32kHz16BitStereo = 31
SAFT44kHz8BitMono = 32
SAFT44kHz8BitStereo = 33
SAFT44kHz16BitMono = 34
SAFT44kHz16BitStereo = 35
SAFT48kHz8BitMono = 36
SAFT48kHz8BitStereo = 37
SAFT48kHz16BitMono = 38
SAFT48kHz16BitStereo = 39
SAFTTrueSpeech_8kHz1BitMono = 40
SAFTCCITT_ALaw_8kHzMono = 41
SAFTCCITT_ALaw_8kHzStereo = 42
SAFTCCITT_ALaw_11kHzMono = 43
SAFTCCITT_ALaw_11kHzStereo = 44
SAFTCCITT_ALaw_22kHzMono = 45
SAFTCCITT_ALaw_22kHzStereo = 46
SAFTCCITT_ALaw_44kHzMono = 47
SAFTCCITT_ALaw_44kHzStereo = 48
SAFTCCITT_uLaw_8kHzMono = 49
SAFTCCITT_uLaw_8kHzStereo = 50
SAFTCCITT_uLaw_11kHzMono = 51
SAFTCCITT_uLaw_11kHzStereo = 52
SAFTCCITT_uLaw_22kHzMono = 53
SAFTCCITT_uLaw_22kHzStereo = 54
SAFTCCITT_uLaw_44kHzMono = 55
SAFTCCITT_uLaw_44kHzStereo = 56
SAFTADPCM_8kHzMono = 57
SAFTADPCM_8kHzStereo = 58
SAFTADPCM_11kHzMono = 59
SAFTADPCM_11kHzStereo = 60
SAFTADPCM_22kHzMono = 61
SAFTADPCM_22kHzStereo = 62
SAFTADPCM_44kHzMono = 63
SAFTADPCM_44kHzStereo = 64
SAFTGSM610_8kHzMono = 65
SAFTGSM610_11kHzMono = 66
SAFTGSM610_22kHzMono = 67
SAFTGSM610_44kHzMono = 68
SpeechAudioFormatType = c_int  # enum


class SpTextSelectionInformation(CoClass):
    "SpTextSelectionInformation Class"
    _reg_clsid_ = GUID("{0F92030A-CBFD-4AB8-A164-FF5985547FF6}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpTextSelectionInformation._com_interfaces_ = [ISpeechTextSelectionInformation]


class ISpeechWaveFormatEx(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IDispatch
):
    _case_insensitive_ = True
    "ISpeechWaveFormatEx Interface"
    _iid_ = GUID("{7A1EF0D5-1581-4741-88E4-209A49F11A10}")
    _idlflags_ = ["dual", "oleautomation"]


ISpeechWaveFormatEx._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("FormatTag"), "propget"],
        HRESULT,
        "FormatTag",
        (["out", "retval"], POINTER(c_short), "FormatTag"),
    ),
    COMMETHOD(
        [dispid(1), helpstring("FormatTag"), "propput"],
        HRESULT,
        "FormatTag",
        (["in"], c_short, "FormatTag"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Channels"), "propget"],
        HRESULT,
        "Channels",
        (["out", "retval"], POINTER(c_short), "Channels"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Channels"), "propput"],
        HRESULT,
        "Channels",
        (["in"], c_short, "Channels"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("SamplesPerSec"), "propget"],
        HRESULT,
        "SamplesPerSec",
        (["out", "retval"], POINTER(c_int), "SamplesPerSec"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("SamplesPerSec"), "propput"],
        HRESULT,
        "SamplesPerSec",
        (["in"], c_int, "SamplesPerSec"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AvgBytesPerSec"), "propget"],
        HRESULT,
        "AvgBytesPerSec",
        (["out", "retval"], POINTER(c_int), "AvgBytesPerSec"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("AvgBytesPerSec"), "propput"],
        HRESULT,
        "AvgBytesPerSec",
        (["in"], c_int, "AvgBytesPerSec"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("BlockAlign"), "propget"],
        HRESULT,
        "BlockAlign",
        (["out", "retval"], POINTER(c_short), "BlockAlign"),
    ),
    COMMETHOD(
        [dispid(5), helpstring("BlockAlign"), "propput"],
        HRESULT,
        "BlockAlign",
        (["in"], c_short, "BlockAlign"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("BitsPerSample"), "propget"],
        HRESULT,
        "BitsPerSample",
        (["out", "retval"], POINTER(c_short), "BitsPerSample"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("BitsPerSample"), "propput"],
        HRESULT,
        "BitsPerSample",
        (["in"], c_short, "BitsPerSample"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("ExtraData"), "propget"],
        HRESULT,
        "ExtraData",
        (["out", "retval"], POINTER(VARIANT), "ExtraData"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("ExtraData"), "propput"],
        HRESULT,
        "ExtraData",
        (["in"], VARIANT, "ExtraData"),
    ),
]
################################################################
## code template for ISpeechWaveFormatEx implementation
##class ISpeechWaveFormatEx_Impl(object):
##    def _get(self):
##        'FormatTag'
##        #return FormatTag
##    def _set(self, FormatTag):
##        'FormatTag'
##    FormatTag = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'Channels'
##        #return Channels
##    def _set(self, Channels):
##        'Channels'
##    Channels = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'SamplesPerSec'
##        #return SamplesPerSec
##    def _set(self, SamplesPerSec):
##        'SamplesPerSec'
##    SamplesPerSec = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'AvgBytesPerSec'
##        #return AvgBytesPerSec
##    def _set(self, AvgBytesPerSec):
##        'AvgBytesPerSec'
##    AvgBytesPerSec = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'BlockAlign'
##        #return BlockAlign
##    def _set(self, BlockAlign):
##        'BlockAlign'
##    BlockAlign = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'BitsPerSample'
##        #return BitsPerSample
##    def _set(self, BitsPerSample):
##        'BitsPerSample'
##    BitsPerSample = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'ExtraData'
##        #return ExtraData
##    def _set(self, ExtraData):
##        'ExtraData'
##    ExtraData = property(_get, _set, doc = _set.__doc__)
##

ISpeechRecoContext._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Recognizer"), "propget"],
        HRESULT,
        "Recognizer",
        (["out", "retval"], POINTER(POINTER(ISpeechRecognizer)), "Recognizer"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("AudioInInterferenceStatus"), "propget"],
        HRESULT,
        "AudioInputInterferenceStatus",
        (["out", "retval"], POINTER(SpeechInterference), "Interference"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("RequestedUIType"), "propget"],
        HRESULT,
        "RequestedUIType",
        (["out", "retval"], POINTER(BSTR), "UIType"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Voice"), "propputref"],
        HRESULT,
        "Voice",
        (["in"], POINTER(ISpeechVoice), "Voice"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Voice"), "propget"],
        HRESULT,
        "Voice",
        (["out", "retval"], POINTER(POINTER(ISpeechVoice)), "Voice"),
    ),
    COMMETHOD(
        [
            dispid(5),
            helpstring("AllowVoiceFormatMatchingOnNextSet"),
            "hidden",
            "propput",
        ],
        HRESULT,
        "AllowVoiceFormatMatchingOnNextSet",
        (["in"], VARIANT_BOOL, "pAllow"),
    ),
    COMMETHOD(
        [
            dispid(5),
            helpstring("AllowVoiceFormatMatchingOnNextSet"),
            "hidden",
            "propget",
        ],
        HRESULT,
        "AllowVoiceFormatMatchingOnNextSet",
        (["out", "retval"], POINTER(VARIANT_BOOL), "pAllow"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("VoicePurgeEvent"), "propput"],
        HRESULT,
        "VoicePurgeEvent",
        (["in"], SpeechRecoEvents, "EventInterest"),
    ),
    COMMETHOD(
        [dispid(6), helpstring("VoicePurgeEvent"), "propget"],
        HRESULT,
        "VoicePurgeEvent",
        (["out", "retval"], POINTER(SpeechRecoEvents), "EventInterest"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("EventInterests"), "propput"],
        HRESULT,
        "EventInterests",
        (["in"], SpeechRecoEvents, "EventInterest"),
    ),
    COMMETHOD(
        [dispid(7), helpstring("EventInterests"), "propget"],
        HRESULT,
        "EventInterests",
        (["out", "retval"], POINTER(SpeechRecoEvents), "EventInterest"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("CmdMaxAlternates"), "propput"],
        HRESULT,
        "CmdMaxAlternates",
        (["in"], c_int, "MaxAlternates"),
    ),
    COMMETHOD(
        [dispid(8), helpstring("CmdMaxAlternates"), "propget"],
        HRESULT,
        "CmdMaxAlternates",
        (["out", "retval"], POINTER(c_int), "MaxAlternates"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("State"), "propput"],
        HRESULT,
        "State",
        (["in"], SpeechRecoContextState, "State"),
    ),
    COMMETHOD(
        [dispid(9), helpstring("State"), "propget"],
        HRESULT,
        "State",
        (["out", "retval"], POINTER(SpeechRecoContextState), "State"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("RetainedAudio"), "propput"],
        HRESULT,
        "RetainedAudio",
        (["in"], SpeechRetainedAudioOptions, "Option"),
    ),
    COMMETHOD(
        [dispid(10), helpstring("RetainedAudio"), "propget"],
        HRESULT,
        "RetainedAudio",
        (["out", "retval"], POINTER(SpeechRetainedAudioOptions), "Option"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("RetainedAudioFormat"), "propputref"],
        HRESULT,
        "RetainedAudioFormat",
        (["in"], POINTER(ISpeechAudioFormat), "Format"),
    ),
    COMMETHOD(
        [dispid(11), helpstring("RetainedAudioFormat"), "propget"],
        HRESULT,
        "RetainedAudioFormat",
        (["out", "retval"], POINTER(POINTER(ISpeechAudioFormat)), "Format"),
    ),
    COMMETHOD([dispid(12), helpstring("Pause")], HRESULT, "Pause"),
    COMMETHOD([dispid(13), helpstring("Resume")], HRESULT, "Resume"),
    COMMETHOD(
        [dispid(14), helpstring("CreateGrammar")],
        HRESULT,
        "CreateGrammar",
        (["in", "optional"], VARIANT, "GrammarId", 0),
        (["out", "retval"], POINTER(POINTER(ISpeechRecoGrammar)), "Grammar"),
    ),
    COMMETHOD(
        [dispid(15), helpstring("CreateResultFromMemory")],
        HRESULT,
        "CreateResultFromMemory",
        (["in"], POINTER(VARIANT), "ResultBlock"),
        (["out", "retval"], POINTER(POINTER(ISpeechRecoResult)), "Result"),
    ),
    COMMETHOD(
        [dispid(16), helpstring("Bookmark")],
        HRESULT,
        "Bookmark",
        (["in"], SpeechBookmarkOptions, "Options"),
        (["in"], VARIANT, "StreamPos"),
        (["in"], VARIANT, "BookmarkId"),
    ),
    COMMETHOD(
        [dispid(17), helpstring("SetAdaptationData")],
        HRESULT,
        "SetAdaptationData",
        (["in"], BSTR, "AdaptationString"),
    ),
]
################################################################
## code template for ISpeechRecoContext implementation
##class ISpeechRecoContext_Impl(object):
##    @property
##    def Recognizer(self):
##        'Recognizer'
##        #return Recognizer
##
##    @property
##    def AudioInputInterferenceStatus(self):
##        'AudioInInterferenceStatus'
##        #return Interference
##
##    @property
##    def RequestedUIType(self):
##        'RequestedUIType'
##        #return UIType
##
##    @property
##    def Voice(self, Voice):
##        'Voice'
##        #return
##
##    def _get(self):
##        'AllowVoiceFormatMatchingOnNextSet'
##        #return pAllow
##    def _set(self, pAllow):
##        'AllowVoiceFormatMatchingOnNextSet'
##    AllowVoiceFormatMatchingOnNextSet = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'VoicePurgeEvent'
##        #return EventInterest
##    def _set(self, EventInterest):
##        'VoicePurgeEvent'
##    VoicePurgeEvent = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'EventInterests'
##        #return EventInterest
##    def _set(self, EventInterest):
##        'EventInterests'
##    EventInterests = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'CmdMaxAlternates'
##        #return MaxAlternates
##    def _set(self, MaxAlternates):
##        'CmdMaxAlternates'
##    CmdMaxAlternates = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'State'
##        #return State
##    def _set(self, State):
##        'State'
##    State = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'RetainedAudio'
##        #return Option
##    def _set(self, Option):
##        'RetainedAudio'
##    RetainedAudio = property(_get, _set, doc = _set.__doc__)
##
##    @property
##    def RetainedAudioFormat(self, Format):
##        'RetainedAudioFormat'
##        #return
##
##    def Pause(self):
##        'Pause'
##        #return
##
##    def Resume(self):
##        'Resume'
##        #return
##
##    def CreateGrammar(self, GrammarId):
##        'CreateGrammar'
##        #return Grammar
##
##    def CreateResultFromMemory(self, ResultBlock):
##        'CreateResultFromMemory'
##        #return Result
##
##    def Bookmark(self, Options, StreamPos, BookmarkId):
##        'Bookmark'
##        #return
##
##    def SetAdaptationData(self, AdaptationString):
##        'SetAdaptationData'
##        #return
##

ISpeechObjectTokens._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Count"), "propget"],
        HRESULT,
        "Count",
        (["out", "retval"], POINTER(c_int), "Count"),
    ),
    COMMETHOD(
        [dispid(0), helpstring("Item")],
        HRESULT,
        "Item",
        (["in"], c_int, "Index"),
        (["out", "retval"], POINTER(POINTER(ISpeechObjectToken)), "Token"),
    ),
    COMMETHOD(
        [dispid(-4), helpstring("Enumerates the tokens"), "restricted", "propget"],
        HRESULT,
        "_NewEnum",
        (["out", "retval"], POINTER(POINTER(IUnknown)), "ppEnumVARIANT"),
    ),
]
################################################################
## code template for ISpeechObjectTokens implementation
##class ISpeechObjectTokens_Impl(object):
##    @property
##    def Count(self):
##        'Count'
##        #return Count
##
##    def Item(self, Index):
##        'Item'
##        #return Token
##
##    @property
##    def _NewEnum(self):
##        'Enumerates the tokens'
##        #return ppEnumVARIANT
##


class SpPhraseInfoBuilder(CoClass):
    "SpPhraseInfoBuilder Class"
    _reg_clsid_ = GUID("{C23FC28D-C55F-4720-8B32-91F73C2BD5D1}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpPhraseInfoBuilder._com_interfaces_ = [ISpeechPhraseInfoBuilder]

SPRECOGNIZERSTATUS._fields_ = [
    ("AudioStatus", SPAUDIOSTATUS),
    ("ullRecognitionStreamPos", c_ulonglong),
    ("ulStreamNumber", c_ulong),
    ("ulNumActive", c_ulong),
    ("ClsidEngine", comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.GUID),
    ("cLangIDs", c_ulong),
    ("aLangID", c_ushort * 20),
    ("ullRecognitionStreamTime", c_ulonglong),
]
assert sizeof(SPRECOGNIZERSTATUS) == 128, sizeof(SPRECOGNIZERSTATUS)
assert alignment(SPRECOGNIZERSTATUS) == 8, alignment(SPRECOGNIZERSTATUS)


class SpAudioFormat(CoClass):
    "SpAudioFormat Class"
    _reg_clsid_ = GUID("{9EF96870-E160-4792-820D-48CF0649E4EC}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpAudioFormat._com_interfaces_ = [ISpeechAudioFormat]


class SpWaveFormatEx(CoClass):
    "SpWaveFormatEx Class"
    _reg_clsid_ = GUID("{C79A574C-63BE-44B9-801F-283F87F898BE}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpWaveFormatEx._com_interfaces_ = [ISpeechWaveFormatEx]


class SpInProcRecoContext(CoClass):
    "SpInProcRecoContext Class"
    _reg_clsid_ = GUID("{73AD6842-ACE0-45E8-A4DD-8795881A2C2A}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpInProcRecoContext._com_interfaces_ = [
    ISpeechRecoContext,
    ISpRecoContext,
    ISpRecoContext2,
    ISpPhoneticAlphabetSelection,
]
SpInProcRecoContext._outgoing_interfaces_ = [_ISpeechRecoContextEvents]


class SpCustomStream(CoClass):
    "SpCustomStream Class"
    _reg_clsid_ = GUID("{8DBEF13F-1948-4AA8-8CF0-048EEBED95D8}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpCustomStream._com_interfaces_ = [ISpeechCustomStream, ISpStream]


class ISpXMLRecoResult(ISpRecoResult):
    _case_insensitive_ = True
    "ISpXMLRecoResult Interface"
    _iid_ = GUID("{AE39362B-45A8-4074-9B9E-CCF49AA2D0B6}")
    _idlflags_ = ["restricted"]


ISpXMLRecoResult._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetXMLResult",
        (["out"], POINTER(WSTRING), "ppszCoMemXMLResult"),
        (["in"], SPXMLRESULTOPTIONS, "Options"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "GetXMLErrorInfo",
        (["out"], POINTER(SPSEMANTICERRORINFO), "pSemanticErrorInfo"),
    ),
]
################################################################
## code template for ISpXMLRecoResult implementation
##class ISpXMLRecoResult_Impl(object):
##    def GetXMLResult(self, Options):
##        '-no docstring-'
##        #return ppszCoMemXMLResult
##
##    def GetXMLErrorInfo(self):
##        '-no docstring-'
##        #return pSemanticErrorInfo
##


class SpFileStream(CoClass):
    "SpFileStream Class"
    _reg_clsid_ = GUID("{947812B3-2AE1-4644-BA86-9E90DED7EC91}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpFileStream._com_interfaces_ = [ISpeechFileStream, ISpStream]


class SpMemoryStream(CoClass):
    "SpMemoryStream Class"
    _reg_clsid_ = GUID("{5FB7EF7D-DFF4-468A-B6B7-2FCBD188F994}")
    _idlflags_ = []
    _typelib_path_ = typelib_path
    _reg_typelib_ = ("{C866CA3A-32F7-11D2-9602-00C04F8EE628}", 5, 4)


SpMemoryStream._com_interfaces_ = [ISpeechMemoryStream, ISpStream]

ISpeechAudioFormat._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("Type"), "propget"],
        HRESULT,
        "Type",
        (["out", "retval"], POINTER(SpeechAudioFormatType), "AudioFormat"),
    ),
    COMMETHOD(
        [dispid(1), helpstring("Type"), "propput"],
        HRESULT,
        "Type",
        (["in"], SpeechAudioFormatType, "AudioFormat"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Guid"), "hidden", "propget"],
        HRESULT,
        "Guid",
        (["out", "retval"], POINTER(BSTR), "Guid"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("Guid"), "hidden", "propput"],
        HRESULT,
        "Guid",
        (["in"], BSTR, "Guid"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("GetWaveFormatEx"), "hidden"],
        HRESULT,
        "GetWaveFormatEx",
        (
            ["out", "retval"],
            POINTER(POINTER(ISpeechWaveFormatEx)),
            "SpeechWaveFormatEx",
        ),
    ),
    COMMETHOD(
        [dispid(4), helpstring("SetWaveFormatEx"), "hidden"],
        HRESULT,
        "SetWaveFormatEx",
        (["in"], POINTER(ISpeechWaveFormatEx), "SpeechWaveFormatEx"),
    ),
]
################################################################
## code template for ISpeechAudioFormat implementation
##class ISpeechAudioFormat_Impl(object):
##    def _get(self):
##        'Type'
##        #return AudioFormat
##    def _set(self, AudioFormat):
##        'Type'
##    Type = property(_get, _set, doc = _set.__doc__)
##
##    def _get(self):
##        'Guid'
##        #return Guid
##    def _set(self, Guid):
##        'Guid'
##    Guid = property(_get, _set, doc = _set.__doc__)
##
##    def GetWaveFormatEx(self):
##        'GetWaveFormatEx'
##        #return SpeechWaveFormatEx
##
##    def SetWaveFormatEx(self, SpeechWaveFormatEx):
##        'SetWaveFormatEx'
##        #return
##

ISpeechPhraseAlternate._methods_ = [
    COMMETHOD(
        [dispid(1), helpstring("RecoResult"), "propget"],
        HRESULT,
        "RecoResult",
        (["out", "retval"], POINTER(POINTER(ISpeechRecoResult)), "RecoResult"),
    ),
    COMMETHOD(
        [dispid(2), helpstring("StartElementInResult"), "propget"],
        HRESULT,
        "StartElementInResult",
        (["out", "retval"], POINTER(c_int), "StartElement"),
    ),
    COMMETHOD(
        [dispid(3), helpstring("NumberOfElementsInResult"), "propget"],
        HRESULT,
        "NumberOfElementsInResult",
        (["out", "retval"], POINTER(c_int), "NumberOfElements"),
    ),
    COMMETHOD(
        [dispid(4), helpstring("Phrase"), "propget"],
        HRESULT,
        "PhraseInfo",
        (["out", "retval"], POINTER(POINTER(ISpeechPhraseInfo)), "PhraseInfo"),
    ),
    COMMETHOD([dispid(5), helpstring("Commit")], HRESULT, "Commit"),
]
################################################################
## code template for ISpeechPhraseAlternate implementation
##class ISpeechPhraseAlternate_Impl(object):
##    @property
##    def RecoResult(self):
##        'RecoResult'
##        #return RecoResult
##
##    @property
##    def StartElementInResult(self):
##        'StartElementInResult'
##        #return StartElement
##
##    @property
##    def NumberOfElementsInResult(self):
##        'NumberOfElementsInResult'
##        #return NumberOfElements
##
##    @property
##    def PhraseInfo(self):
##        'Phrase'
##        #return PhraseInfo
##
##    def Commit(self):
##        'Commit'
##        #return
##


class ISpRecoGrammar2(
    comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0.IUnknown
):
    _case_insensitive_ = True
    "ISpRecoGrammar2 Interface"
    _iid_ = GUID("{4B37BC9E-9ED6-44A3-93D3-18F022B79EC3}")
    _idlflags_ = ["restricted"]


ISpRecoGrammar2._methods_ = [
    COMMETHOD(
        [],
        HRESULT,
        "GetRules",
        (["out"], POINTER(POINTER(SPRULE)), "ppCoMemRules"),
        (["out"], POINTER(c_uint), "puNumRules"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadCmdFromFile2",
        (["in"], WSTRING, "pszFileName"),
        (["in"], SPLOADOPTIONS, "Options"),
        (["in"], WSTRING, "pszSharingUri"),
        (["in"], WSTRING, "pszBaseUri"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "LoadCmdFromMemory2",
        (["in"], POINTER(SPBINARYGRAMMAR), "pGrammar"),
        (["in"], SPLOADOPTIONS, "Options"),
        (["in"], WSTRING, "pszSharingUri"),
        (["in"], WSTRING, "pszBaseUri"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetRulePriority",
        (["in"], WSTRING, "pszRuleName"),
        (["in"], c_ulong, "ulRuleId"),
        (["in"], c_int, "nRulePriority"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetRuleWeight",
        (["in"], WSTRING, "pszRuleName"),
        (["in"], c_ulong, "ulRuleId"),
        (["in"], c_float, "flWeight"),
    ),
    COMMETHOD([], HRESULT, "SetDictationWeight", (["in"], c_float, "flWeight")),
    COMMETHOD(
        [],
        HRESULT,
        "SetGrammarLoader",
        (["in"], POINTER(ISpeechResourceLoader), "pLoader"),
    ),
    COMMETHOD(
        [],
        HRESULT,
        "SetSMLSecurityManager",
        (["in"], POINTER(IInternetSecurityManager), "pSMLSecurityManager"),
    ),
]
################################################################
## code template for ISpRecoGrammar2 implementation
##class ISpRecoGrammar2_Impl(object):
##    def GetRules(self):
##        '-no docstring-'
##        #return ppCoMemRules, puNumRules
##
##    def LoadCmdFromFile2(self, pszFileName, Options, pszSharingUri, pszBaseUri):
##        '-no docstring-'
##        #return
##
##    def LoadCmdFromMemory2(self, pGrammar, Options, pszSharingUri, pszBaseUri):
##        '-no docstring-'
##        #return
##
##    def SetRulePriority(self, pszRuleName, ulRuleId, nRulePriority):
##        '-no docstring-'
##        #return
##
##    def SetRuleWeight(self, pszRuleName, ulRuleId, flWeight):
##        '-no docstring-'
##        #return
##
##    def SetDictationWeight(self, flWeight):
##        '-no docstring-'
##        #return
##
##    def SetGrammarLoader(self, pLoader):
##        '-no docstring-'
##        #return
##
##    def SetSMLSecurityManager(self, pSMLSecurityManager):
##        '-no docstring-'
##        #return
##

__all__ = [
    "SPPHRASEELEMENT",
    "DISPID_SLPPartOfSpeech",
    "SINone",
    "DISPID_SRGCmdSetRuleIdState",
    "SPWT_LEXICAL",
    "SDTProperty",
    "SPFILEMODE",
    "DISPID_SPPEngineConfidence",
    "SPWF_INPUT",
    "DISPID_SRCState",
    "DISPID_SRGState",
    "DISPID_SPERetainedSizeBytes",
    "DISPID_SpeechPhraseElement",
    "DISPID_SpeechVoiceStatus",
    "SPEVENTSOURCEINFO",
    "DISPID_SpeechLexiconWord",
    "SAFT24kHz8BitMono",
    "SECFIgnoreKanaType",
    "DISPID_SRGId",
    "DISPID_SRRDiscardResultInfo",
    "SAFT8kHz16BitMono",
    "SpeechCategoryAppLexicons",
    "DISPID_SPRs_NewEnum",
    "SPDKL_CurrentUser",
    "DISPID_SAFGuid",
    "DISPID_SGRAttributes",
    "SpAudioFormat",
    "SAFTTrueSpeech_8kHz1BitMono",
    "SGSEnabled",
    "SGRSTTEpsilon",
    "DISPID_SpeechPhraseReplacements",
    "DISPID_SOTIsUISupported",
    "DISPID_SPIAudioSizeBytes",
    "SPGS_EXCLUSIVE",
    "SAFTCCITT_uLaw_22kHzStereo",
    "DISPID_SRRPhraseInfo",
    "SPEI_MAX_TTS",
    "_ISpeechRecoContextEvents",
    "DISPID_SpeechDataKey",
    "SDA_Two_Trailing_Spaces",
    "ISpRecognizer2",
    "DISPID_SpeechRecognizerStatus",
    "DISPID_SRGCmdLoadFromFile",
    "ISpeechGrammarRuleState",
    "DISPID_SRCEEnginePrivate",
    "SPINTERFERENCE_TOOSLOW",
    "SpeechAudioVolume",
    "SpeechRunState",
    "DISPID_SpeechPhraseElements",
    "DISPID_SOTGetDescription",
    "SPEI_PHONEME",
    "SLTUser",
    "SPPS_RESERVED2",
    "SAFT16kHz8BitMono",
    "SVP_0",
    "DISPID_SFSClose",
    "tagSPPROPERTYINFO",
    "IEnumString",
    "DISPID_SPILanguageId",
    "DISPID_SRDisplayUI",
    "DISPID_SGRsCommit",
    "ISpStream",
    "SPSTREAMFORMATTYPE",
    "SpeechTokenIdUserLexicon",
    "SpeechPartOfSpeech",
    "DISPID_SpeechPhraseAlternate",
    "SpInprocRecognizer",
    "DISPID_SLWsItem",
    "ISpObjectWithToken",
    "SPEI_SR_PRIVATE",
    "DISPID_SLRemovePronunciationByPhoneIds",
    "UINT_PTR",
    "eLEXTYPE_PRIVATE7",
    "DISPID_SRSSupportedLanguages",
    "SRSActive",
    "ISpeechLexicon",
    "DISPID_SWFEAvgBytesPerSec",
    "SPAUDIOBUFFERINFO",
    "SPWT_LEXICAL_NO_SPECIAL_CHARS",
    "DISPID_SMSGetData",
    "DISPID_SVVolume",
    "DISPID_SVSVisemeId",
    "eLEXTYPE_PRIVATE10",
    "SAFT44kHz8BitStereo",
    "DISPID_SRCAudioInInterferenceStatus",
    "SpeechRetainedAudioOptions",
    "SRTExtendableParse",
    "DISPID_SpeechWaveFormatEx",
    "STCInprocHandler",
    "ISpeechPhraseRule",
    "SPAR_High",
    "SAFT11kHz16BitStereo",
    "DISPID_SRGetFormat",
    "SAFTADPCM_11kHzStereo",
    "STCInprocServer",
    "DISPID_SVSCurrentStreamNumber",
    "DISPID_SLWPronunciations",
    "DISPID_SPIStartTime",
    "SPEI_MIN_TTS",
    "SP_VISEME_16",
    "SPEI_RESERVED5",
    "SpNullPhoneConverter",
    "SAFTCCITT_ALaw_8kHzStereo",
    "DISPID_SVSRunningState",
    "SP_VISEME_11",
    "SVP_15",
    "DISPID_SOTId",
    "eLEXTYPE_MORPHOLOGY",
    "SAFTGSM610_11kHzMono",
    "SVSFIsNotXML",
    "SRTAutopause",
    "SVEViseme",
    "DISPID_SMSAMMHandle",
    "SPSLMA",
    "DISPID_SDKCreateKey",
    "DISPID_SpeechPhoneConverter",
    "SpeechCategoryPhoneConverters",
    "SAFT8kHz8BitMono",
    "eLEXTYPE_PRIVATE4",
    "SpeechGrammarTagDictation",
    "DISPID_SPANumberOfElementsInResult",
    "DISPID_SPEAudioTimeOffset",
    "SASStop",
    "SDKLLocalMachine",
    "SVSFNLPMask",
    "DISPID_SOTRemoveStorageFileName",
    "SpeechTokenKeyAttributes",
    "SAFT32kHz16BitMono",
    "DISPID_SpeechLexiconWords",
    "DISPID_SPPBRestorePhraseFromMemory",
    "SAFT32kHz8BitStereo",
    "DISPID_SLWsCount",
    "DISPID_SGRSTsCount",
    "SPSNoun",
    "DISPIDSPTSI_SelectionOffset",
    "SVEWordBoundary",
    "SPRST_INACTIVE_WITH_PURGE",
    "DISPID_SPISaveToMemory",
    "SpStream",
    "DISPID_SLPType",
    "SLTApp",
    "DISPID_SOTRemove",
    "SDTDisplayText",
    "SVEAllEvents",
    "DISPID_SRGetPropertyString",
    "DISPID_SDKSetStringValue",
    "SpeechAddRemoveWord",
    "SpeechWordPronounceable",
    "DISPID_SVSInputWordPosition",
    "DISPID_SVSpeakCompleteEvent",
    "Speech_StreamPos_Asap",
    "DISPID_SRCESoundStart",
    "SPWORDPRONOUNCEABLE",
    "IInternetSecurityMgrSite",
    "DISPID_SOTGetAttribute",
    "DISPID_SRCEPropertyNumberChange",
    "DISPID_SpeechPhraseInfo",
    "SAFTGSM610_44kHzMono",
    "ISpeechPhraseReplacement",
    "DISPID_SVPriority",
    "SAFTADPCM_8kHzStereo",
    "DISPID_SRGCmdLoadFromProprietaryGrammar",
    "DISPID_SREmulateRecognition",
    "DISPID_SpeechGrammarRules",
    "DISPID_SRGCmdLoadFromObject",
    "ISpPhoneConverter",
    "SAFTCCITT_ALaw_22kHzStereo",
    "DISPID_SDKEnumValues",
    "SPWT_PRONUNCIATION",
    "ISpXMLRecoResult",
    "DISPID_SRCRecognizer",
    "DISPID_SABIEventBias",
    "DISPID_SPIRule",
    "SREAllEvents",
    "_RemotableHandle",
    "ISpeechGrammarRules",
    "DISPID_SRIsShared",
    "DISPID_SGRSTPropertyName",
    "DISPID_SVVoice",
    "SAFTNoAssignedFormat",
    "SPINTERFERENCE_TOOLOUD",
    "DISPID_SRCRetainedAudioFormat",
    "DISPID_SRRSaveToMemory",
    "SPRS_INACTIVE",
    "SPAS_RUN",
    "DISPID_SPPName",
    "SpeechEmulationCompareFlags",
    "DISPID_SpeechPhraseProperties",
    "SVP_8",
    "DISPID_SCSBaseStream",
    "STSF_LocalAppData",
    "SAFT24kHz8BitStereo",
    "SpeechDisplayAttributes",
    "DISPID_SpeechAudio",
    "SPEI_RESERVED3",
    "SPGS_DISABLED",
    "eLEXTYPE_PRIVATE18",
    "DISPID_SPIElements",
    "SDTAudio",
    "SAFT44kHz8BitMono",
    "DISPID_SDKGetlongValue",
    "ISpeechPhraseElements",
    "SpMMAudioIn",
    "SVSFParseSapi",
    "SRERequestUI",
    "SSFMOpenForRead",
    "SAFT11kHz8BitMono",
    "SREPropertyStringChange",
    "DISPID_SPPsItem",
    "SpeechSpecialTransitionType",
    "DISPID_SpeechRecoResultTimes",
    "ISpPhraseAlt",
    "SpeechEngineProperties",
    "SDA_Consume_Leading_Spaces",
    "SPSHT_EMAIL",
    "DISPIDSPTSI_ActiveLength",
    "DISPID_SRCCmdMaxAlternates",
    "SpSharedRecognizer",
    "eLEXTYPE_PRIVATE3",
    "SGRSTTTextBuffer",
    "SPPS_Modifier",
    "ISpeechTextSelectionInformation",
    "ISpeechFileStream",
    "ISpeechLexiconPronunciations",
    "SPLO_STATIC",
    "SpeechRecoProfileProperties",
    "SPBO_AHEAD",
    "SITooLoud",
    "SPPS_LMA",
    "SpeechTokenShellFolder",
    "SPDKL_LocalMachine",
    "DISPID_SPACommit",
    "DISPID_SGRsItem",
    "DISPID_SRProfile",
    "SPEI_RESERVED1",
    "SpeechGrammarWordType",
    "SVEEndInputStream",
    "SRTReSent",
    "SPPS_Unknown",
    "SSFMCreate",
    "SWPUnknownWordUnpronounceable",
    "DISPID_SPEPronunciation",
    "DISPID_SpeechGrammarRule",
    "DISPID_SpeechLexiconProns",
    "DISPID_SVSpeak",
    "SPEI_SOUND_END",
    "SPWORDLIST",
    "DISPID_SVStatus",
    "ISpeechResourceLoader",
    "DISPID_SRAudioInput",
    "SpeechRuleAttributes",
    "DISPID_SRGRules",
    "SVSFDefault",
    "DISPID_SDKDeleteValue",
    "DISPID_SPPId",
    "SVEStartInputStream",
    "DISPID_SRCResume",
    "SPSHORTCUTPAIR",
    "SPVPRIORITY",
    "DISPID_SVSpeakStream",
    "DISPID_SRCEInterference",
    "ISpeechGrammarRuleStateTransition",
    "SREInterference",
    "SPEI_START_INPUT_STREAM",
    "DISPID_SGRSTsItem",
    "SRSInactiveWithPurge",
    "SSTTDictation",
    "DISPID_SPELexicalForm",
    "DISPID_SPPNumberOfElements",
    "SPPS_Verb",
    "SPPARTOFSPEECH",
    "DISPID_SRRTTickCount",
    "eLEXTYPE_PRIVATE6",
    "DISPID_SRGDictationLoad",
    "SAFTNonStandardFormat",
    "SPEI_SOUND_START",
    "DISPID_SOTCGetDataKey",
    "DISPID_SGRSTs_NewEnum",
    "tagSTATSTG",
    "DISPID_SOTDisplayUI",
    "SPINTERFERENCE_NOISE",
    "SECFDefault",
    "__MIDL___MIDL_itf_sapi_0000_0020_0001",
    "DISPID_SVEStreamEnd",
    "SRTSMLTimeout",
    "DISPID_SGRSTransitions",
    "DISPID_SASCurrentSeekPosition",
    "DISPID_SRCEPhraseStart",
    "SpeechPropertyHighConfidenceThreshold",
    "DISPID_SVGetProfiles",
    "ISpeechObjectTokenCategory",
    "DISPID_SRState",
    "SPEI_PROPERTY_STRING_CHANGE",
    "SRADefaultToActive",
    "DISPID_SpeechCustomStream",
    "ISpProperties",
    "SVEBookmark",
    "SPSHT_Unknown",
    "DISPID_SGRs_NewEnum",
    "SPSEMANTICFORMAT",
    "DISPID_SPCIdToPhone",
    "SVPNormal",
    "SpeechVoiceEvents",
    "DISPID_SpeechPhraseReplacement",
    "SPPS_RESERVED3",
    "SGLexical",
    "DISPID_SVAllowAudioOuputFormatChangesOnNextSet",
    "SPEI_MAX_SR",
    "ISpeechPhraseInfoBuilder",
    "SPEI_RECOGNITION",
    "DISPID_SPEAudioStreamOffset",
    "SpeechGrammarTagWildcard",
    "SVSFIsFilename",
    "DISPID_SVIsUISupported",
    "SAFTADPCM_44kHzStereo",
    "eLEXTYPE_LETTERTOSOUND",
    "SPAS_PAUSE",
    "DISPID_SOTMatchesAttributes",
    "eLEXTYPE_PRIVATE9",
    "SVEPrivate",
    "DISPID_SVSyncronousSpeakTimeout",
    "SPCT_COMMAND",
    "SBONone",
    "ISpeechGrammarRuleStateTransitions",
    "DISPID_SPRuleConfidence",
    "DISPID_SGRSTRule",
    "SVSFVoiceMask",
    "DISPID_SRGDictationSetState",
    "eLEXTYPE_PRIVATE8",
    "DISPID_SRSetPropertyString",
    "SpObjectTokenCategory",
    "SPINTERFERENCE_LATENCY_TRUNCATE_END",
    "DISPID_SLPs_NewEnum",
    "SAFT48kHz8BitStereo",
    "DISPID_SRCEPropertyStringChange",
    "ISpeechDataKey",
    "SPAUDIOSTATUS",
    "SpeechCategoryRecognizers",
    "SAFT8kHz8BitStereo",
    "SPAUDIOOPTIONS",
    "SpeechLoadOption",
    "SPPHRASERULE",
    "SFTSREngine",
    "DISPID_SPIEnginePrivateData",
    "DISPID_SASNonBlockingIO",
    "DISPID_SpeechRecognizer",
    "SpeechPropertyResponseSpeed",
    "SRAONone",
    "SREPhraseStart",
    "SPPS_RESERVED1",
    "SPEI_SENTENCE_BOUNDARY",
    "SP_VISEME_3",
    "DISPID_SWFEExtraData",
    "SP_VISEME_15",
    "SPSHORTCUTPAIRLIST",
    "SRAExport",
    "eLEXTYPE_RESERVED8",
    "SRERecoOtherContext",
    "ISpeechObjectToken",
    "SpeechStreamFileMode",
    "SP_VISEME_0",
    "DISPID_SpeechObjectTokenCategory",
    "SpShortcut",
    "SGPronounciation",
    "DISPID_SRRAudio",
    "SAFT48kHz8BitMono",
    "SPAR_Medium",
    "SpUnCompressedLexicon",
    "SPRECOCONTEXTSTATUS",
    "SpeechFormatType",
    "ISpPhoneticAlphabetSelection",
    "ISpeechRecognizer",
    "SAFTCCITT_ALaw_44kHzStereo",
    "SPFM_OPEN_READWRITE",
    "SpeechAudioProperties",
    "DISPID_SRRTOffsetFromStart",
    "SpTextSelectionInformation",
    "DISPID_SASFreeBufferSpace",
    "SpeechVoiceSpeakFlags",
    "SRSEIsSpeaking",
    "DISPID_SpeechAudioBufferInfo",
    "SpPhoneticAlphabetConverter",
    "eLEXTYPE_PRIVATE11",
    "SAFTCCITT_uLaw_11kHzMono",
    "DISPID_SVEPhoneme",
    "SSSPTRelativeToEnd",
    "DISPID_SPRuleFirstElement",
    "ISpeechRecoResult2",
    "DISPID_SRIsUISupported",
    "SECFEmulateResult",
    "eLEXTYPE_RESERVED4",
    "DISPID_SRGCmdLoadFromMemory",
    "SPSNotOverriden",
    "SPPS_Noun",
    "DISPID_SPIAudioSizeTime",
    "DISPID_SRCRetainedAudio",
    "DISPID_SABufferNotifySize",
    "SDTRule",
    "SRCS_Disabled",
    "SAFT12kHz16BitStereo",
    "ISpStreamFormatConverter",
    "ISpeechRecoResultDispatch",
    "SpeechRegistryUserRoot",
    "SPEI_FALSE_RECOGNITION",
    "DISPID_SGRInitialState",
    "SPWT_DISPLAY",
    "SPWP_KNOWN_WORD_PRONOUNCEABLE",
    "eLEXTYPE_RESERVED7",
    "DISPID_SVSkip",
    "DISPID_SRGRecoContext",
    "SPGRAMMARSTATE",
    "SVSFlagsAsync",
    "DISPID_SVAlertBoundary",
    "DISPID_SOTCEnumerateTokens",
    "SPEI_END_SR_STREAM",
    "SAFTGSM610_22kHzMono",
    "SpeechGrammarRuleStateTransitionType",
    "DISPID_SpeechAudioStatus",
    "DISPID_SBSRead",
    "SPSHORTCUTTYPE",
    "DISPID_SABufferInfo",
    "SPEI_RECO_OTHER_CONTEXT",
    "DISPID_SpeechPhraseRules",
    "SDA_One_Trailing_Space",
    "DISPID_SRCESoundEnd",
    "DISPID_SASState",
    "SPCT_DICTATION",
    "ISpeechAudioFormat",
    "DISPID_SLGenerationId",
    "SP_VISEME_13",
    "SPAR_Unknown",
    "DISPID_SPIGetText",
    "SVSFIsXML",
    "DISPID_SRRAlternates",
    "SPEI_RESERVED2",
    "ISpeechPhraseElement",
    "DISPID_SPIGrammarId",
    "SpeechVoicePriority",
    "DISPID_SVEventInterests",
    "DISPID_SPEDisplayText",
    "SVP_11",
    "ISpDataKey",
    "DISPID_SGRSTPropertyId",
    "SVP_5",
    "ISpRecoContext",
    "DISPID_SWFEChannels",
    "DISPID_SVSInputSentenceLength",
    "SAFTADPCM_22kHzStereo",
    "DISPID_SRSAudioStatus",
    "ISpeechPhoneConverter",
    "SPDATAKEYLOCATION",
    "SGDSActiveWithAutoPause",
    "SRESoundStart",
    "DISPID_SpeechObjectTokens",
    "DISPID_SVEStreamStart",
    "SPSMF_SRGS_SAPIPROPERTIES",
    "SGLexicalNoSpecialChars",
    "SPRS_ACTIVE_USER_DELIMITED",
    "SPRST_ACTIVE",
    "DISPID_SpeechRecoContextEvents",
    "DISPID_SGRsCount",
    "eLEXTYPE_PRIVATE2",
    "DISPID_SPEAudioSizeTime",
    "DISPID_SRRTLength",
    "SAFT22kHz16BitMono",
    "ISpEventSink",
    "DISPID_SVSInputSentencePosition",
    "SPEI_START_SR_STREAM",
    "SREPropertyNumChange",
    "SPPS_NotOverriden",
    "DISPID_SLPLangId",
    "SAFTExtendedAudioFormat",
    "SP_VISEME_19",
    "DISPID_SWFEBitsPerSample",
    "ISpeechObjectTokens",
    "SP_VISEME_6",
    "ISpObjectTokenCategory",
    "ISpeechPhraseInfo",
    "SITooQuiet",
    "SGRSTTWord",
    "DISPID_SLRemovePronunciation",
    "DISPID_SPCPhoneToId",
    "SpeechTokenContext",
    "SVP_10",
    "SLOStatic",
    "ISpeechPhraseProperties",
    "DISPID_SRCEEndStream",
    "DISPID_SRCVoice",
    "SPRS_ACTIVE",
    "DISPID_SRGReset",
    "SPEI_WORD_BOUNDARY",
    "SAFT11kHz8BitStereo",
    "DISPID_SPRDisplayAttributes",
    "SAFT22kHz8BitMono",
    "SPCT_SUB_COMMAND",
    "DISPID_SGRSRule",
    "SVP_2",
    "SP_VISEME_10",
    "DISPID_SRStatus",
    "_SPAUDIOSTATE",
    "eLEXTYPE_PRIVATE16",
    "DISPID_SPIProperties",
    "SDTReplacement",
    "SAFTCCITT_uLaw_22kHzMono",
    "LONG_PTR",
    "DISPID_SWFESamplesPerSec",
    "SRERecognition",
    "SVP_6",
    "SpSharedRecoContext",
    "SPGS_ENABLED",
    "DISPID_SRCERecognitionForOtherContext",
    "DISPID_SRAudioInputStream",
    "eLEXTYPE_APP",
    "ISpLexicon",
    "DISPID_SPRuleParent",
    "SVF_Emphasis",
    "SP_VISEME_20",
    "SpeechVisemeType",
    "DISPID_SBSWrite",
    "SPSERIALIZEDPHRASE",
    "DISPID_SPPsCount",
    "SpeechPropertyComplexResponseSpeed",
    "ISpNotifySink",
    "SP_VISEME_21",
    "DISPID_SRGIsPronounceable",
    "DISPID_SMSADeviceId",
    "SPGRAMMARWORDTYPE",
    "SGRSTTRule",
    "ISpeechRecognizerStatus",
    "DISPID_SGRSTWeight",
    "SP_VISEME_18",
    "SAFTText",
    "SRESoundEnd",
    "SpeechRecognitionType",
    "SPWAVEFORMATTYPE",
    "SP_VISEME_5",
    "SPSEMANTICERRORINFO",
    "SpeechGrammarState",
    "SPRECORESULTTIMES",
    "DISPID_SRRGetXMLResult",
    "DISPID_SWFEBlockAlign",
    "DISPID_SVGetVoices",
    "SpObjectToken",
    "DISPID_SAFGetWaveFormatEx",
    "SPFM_NUM_MODES",
    "DISPID_SOTsCount",
    "DISPID_SPIReplacements",
    "SASClosed",
    "DISPID_SLGetWords",
    "SpCompressedLexicon",
    "ISpeechAudioBufferInfo",
    "DISPID_SpeechPhraseProperty",
    "IInternetSecurityManager",
    "DISPID_SOTCDefault",
    "SPINTERFERENCE_NONE",
    "DISPID_SDKSetLongValue",
    "DISPID_SDKGetBinaryValue",
    "eLEXTYPE_PRIVATE14",
    "SAFTCCITT_ALaw_11kHzStereo",
    "SpeechAudioState",
    "ISpAudio",
    "SDKLCurrentConfig",
    "eLEXTYPE_RESERVED6",
    "DISPID_SMSALineId",
    "DISPID_SVEEnginePrivate",
    "SAFTCCITT_uLaw_44kHzStereo",
    "SPVPRI_NORMAL",
    "DISPIDSPTSI",
    "DISPID_SPRules_NewEnum",
    "SRSActiveAlways",
    "SpMMAudioEnum",
    "STCRemoteServer",
    "SPSUnknown",
    "DISPID_SRSCurrentStreamNumber",
    "DISPID_SRCPause",
    "SRADynamic",
    "SECHighConfidence",
    "SpeechGrammarTagUnlimitedDictation",
    "SpeechDictationTopicSpelling",
    "SpeechAudioFormatGUIDText",
    "SPVPRI_ALERT",
    "SPCATEGORYTYPE",
    "DISPID_SRCEStartStream",
    "SPWORDPRONUNCIATION",
    "DISPID_SpeechVoiceEvent",
    "DISPID_SPERequiredConfidence",
    "DISPID_SPEEngineConfidence",
    "DISPID_SLPsItem",
    "SPEI_PROPERTY_NUM_CHANGE",
    "SPEI_END_INPUT_STREAM",
    "SPINTERFERENCE",
    "SP_VISEME_8",
    "SPAS_STOP",
    "SPRECOGNIZERSTATUS",
    "SPWORDTYPE",
    "SpeechInterference",
    "SpeechWordType",
    "SPDKL_CurrentConfig",
    "DISPID_SPIRetainedSizeBytes",
    "SVP_1",
    "DISPID_SOTsItem",
    "ISpObjectToken",
    "SpeechDataKeyLocation",
    "DISPID_SPERetainedStreamOffset",
    "SPSHT_OTHER",
    "DISPID_SGRsFindRule",
    "DISPID_SPRFirstElement",
    "SSFMOpenReadWrite",
    "_ISpeechVoiceEvents",
    "SpFileStream",
    "DISPID_SLGetGenerationChange",
    "SVSFUnusedFlags",
    "DISPID_SGRSTText",
    "DISPID_SRGSetWordSequenceData",
    "SpeechAllElements",
    "SVSFPersistXML",
    "DISPID_SLPPhoneIds",
    "SREStreamStart",
    "DISPID_SDKSetBinaryValue",
    "SpVoice",
    "SPAR_Low",
    "SpeechEngineConfidence",
    "DISPID_SRCBookmark",
    "SPSSuppressWord",
    "DISPID_SRSNumberOfActiveRules",
    "SASRun",
    "SAFT16kHz8BitStereo",
    "DISPID_SPRText",
    "DISPID_SRCSetAdaptationData",
    "DISPID_SLWs_NewEnum",
    "DISPID_SGRAddResource",
    "SP_VISEME_2",
    "STSF_CommonAppData",
    "DISPID_SBSSeek",
    "DISPID_SRGCmdSetRuleState",
    "ISpResourceManager",
    "DISPID_SPIEngineId",
    "SGDisplay",
    "DISPID_SPPValue",
    "DISPID_SPRNumberOfElements",
    "DISPID_SVRate",
    "SPXRO_SML",
    "SPSERIALIZEDRESULT",
    "DISPID_SADefaultFormat",
    "SAFT12kHz8BitMono",
    "SpInProcRecoContext",
    "SPSInterjection",
    "SpeechPropertyAdaptationOn",
    "SpeechPropertyResourceUsage",
    "SVP_18",
    "SVF_Stressed",
    "SGSExclusive",
    "DISPID_SLWLangId",
    "DISPID_SRRGetXMLErrorInfo",
    "SPXMLRESULTOPTIONS",
    "SpeechAudioFormatGUIDWave",
    "SPCS_DISABLED",
    "DISPID_SGRsCommitAndSave",
    "SVP_13",
    "SpNotifyTranslator",
    "DISPID_SOTCreateInstance",
    "SPEI_TTS_AUDIO_LEVEL",
    "DISPID_SFSOpen",
    "DISPID_SRRecognizer",
    "SPSModifier",
    "SP_VISEME_7",
    "SPPS_Noncontent",
    "Speech_StreamPos_RealTime",
    "DISPID_SGRClear",
    "SAFT12kHz16BitMono",
    "DISPID_SPAs_NewEnum",
    "DISPID_SLAddPronunciation",
    "SVPAlert",
    "DISPID_SGRSTType",
    "SAFT12kHz8BitStereo",
    "DISPID_SVEViseme",
    "DISPID_SGRName",
    "SpeechCategoryRecoProfiles",
    "DISPID_SAEventHandle",
    "SPSHT_NotOverriden",
    "DISPIDSPTSI_ActiveOffset",
    "SPSVerb",
    "DISPID_SAFSetWaveFormatEx",
    "DISPID_SPRuleName",
    "SECNormalConfidence",
    "DISPIDSPRG",
    "SPRULESTATE",
    "DISPID_SBSFormat",
    "DISPID_SRCCreateResultFromMemory",
    "DISPID_SpeechRecoContext",
    "SWPUnknownWordPronounceable",
    "DISPID_SPRulesCount",
    "DISPID_SOTCategory",
    "SPPHRASE",
    "DISPID_SPIGetDisplayAttributes",
    "ISpRecoResult",
    "SAFT8kHz16BitStereo",
    "SPEI_PHRASE_START",
    "DISPID_SOTCSetId",
    "DISPID_SGRAddState",
    "IEnumSpObjectTokens",
    "SPSMF_UPS",
    "ISpeechPhraseAlternate",
    "SPPS_RESERVED4",
    "SAFT16kHz16BitMono",
    "SREAudioLevel",
    "DISPID_SRGetRecognizers",
    "SAFT32kHz16BitStereo",
    "eLEXTYPE_PRIVATE19",
    "SRAORetainAudio",
    "SpeechRegistryLocalMachineRoot",
    "DISPID_SLWType",
    "SPPS_Interjection",
    "SPFM_CREATE",
    "SPLEXICONTYPE",
    "ISpRecoCategory",
    "DISPID_SPARecoResult",
    "SPAO_RETAIN_AUDIO",
    "DISPID_SGRId",
    "SAFTCCITT_uLaw_44kHzMono",
    "SVP_9",
    "SVP_19",
    "Speech_Max_Pron_Length",
    "DISPID_SVSPhonemeId",
    "SPDKL_DefaultLocation",
    "DISPID_SpeechMemoryStream",
    "SpeechVisemeFeature",
    "SPRST_INACTIVE",
    "SREStreamEnd",
    "ISpeechLexiconPronunciation",
    "DISPID_SVSLastBookmark",
    "ISpeechGrammarRule",
    "SECFIgnoreCase",
    "SpResourceManager",
    "SAFT22kHz8BitStereo",
    "SSSPTRelativeToCurrentPosition",
    "SPEI_REQUEST_UI",
    "eWORDTYPE_ADDED",
    "SDKLDefaultLocation",
    "SDTAlternates",
    "SPEI_TTS_BOOKMARK",
    "DISPID_SRGDictationUnload",
    "SREBookmark",
    "SpeechBookmarkOptions",
    "DISPID_SPEsCount",
    "DISPID_SpeechLexicon",
    "SPBINARYGRAMMAR",
    "SRSInactive",
    "ISpeechMemoryStream",
    "SPEI_SR_RETAINEDAUDIO",
    "SBOPause",
    "SVP_17",
    "DISPID_SPPParent",
    "SINoSignal",
    "SPEI_SR_AUDIO_LEVEL",
    "SPWF_SRENGINE",
    "ISequentialStream",
    "DISPID_SpeechObjectToken",
    "SDA_No_Trailing_Space",
    "__MIDL___MIDL_itf_sapi_0000_0020_0002",
    "DISPID_SPEs_NewEnum",
    "SP_VISEME_14",
    "ISpRecognizer3",
    "SVP_4",
    "ISpeechVoiceStatus",
    "DISPID_SRCERecognition",
    "DISPID_SPAsItem",
    "SPEVENTENUM",
    "ISpeechBaseStream",
    "SpeechVoiceSkipTypeSentence",
    "DISPID_SDKEnumKeys",
    "SVSFParseSsml",
    "SPSMF_SRGS_SEMANTICINTERPRETATION_MS",
    "DISPID_SGRSTNextState",
    "SpStreamFormatConverter",
    "DISPID_SPEDisplayAttributes",
    "SPCT_SLEEP",
    "SPBO_NONE",
    "DISPID_SVPause",
    "SpeechVoiceCategoryTTSRate",
    "DISPID_SLPsCount",
    "SPEI_MIN_SR",
    "eLEXTYPE_USER_SHORTCUT",
    "SpeechCategoryAudioIn",
    "DISPID_SDKDeleteKey",
    "SpeechPropertyLowConfidenceThreshold",
    "Speech_Max_Word_Length",
    "SPEI_VISEME",
    "SPLOADOPTIONS",
    "DISPID_SpeechPhraseAlternates",
    "SAFT48kHz16BitStereo",
    "SGSDisabled",
    "SRTEmulated",
    "SPBO_PAUSE",
    "SPEI_UNDEFINED",
    "SAFT44kHz16BitStereo",
    "SPCT_SUB_DICTATION",
    "DISPID_SPAStartElementInResult",
    "DISPID_SRRAudioFormat",
    "DISPID_SVGetAudioOutputs",
    "SP_VISEME_9",
    "SpeechTokenKeyFiles",
    "SpeechRecoContextState",
    "SPEI_RECO_STATE_CHANGE",
    "ISpeechRecoResult",
    "DISPID_SpeechGrammarRuleState",
    "SAFTCCITT_ALaw_8kHzMono",
    "DISPID_SVESentenceBoundary",
    "DISPID_SAFType",
    "SRAImport",
    "DISPID_SRCERequestUI",
    "ISpPhoneticAlphabetConverter",
    "ISpeechVoice",
    "SAFTDefault",
    "SPAUDIOSTATE",
    "DISPID_SRCCreateGrammar",
    "SpeechRuleState",
    "SREFalseRecognition",
    "DISPID_SRAllowVoiceFormatMatchingOnNextSet",
    "SPEI_VOICE_CHANGE",
    "SpMemoryStream",
    "DISPID_SRSetPropertyNumber",
    "SpeechCategoryVoices",
    "DISPID_SRCEFalseRecognition",
    "DISPID_SOTGetStorageFileName",
    "IStream",
    "DISPID_SVDisplayUI",
    "SPEI_INTERFERENCE",
    "DISPID_SPAPhraseInfo",
    "SAFTCCITT_ALaw_44kHzMono",
    "SFTInput",
    "SPAS_CLOSED",
    "DISPID_SRGetPropertyNumber",
    "SPRECOSTATE",
    "DISPID_SRSCurrentStreamPosition",
    "ISpRecognizer",
    "DISPID_SMSSetData",
    "SPRS_ACTIVE_WITH_AUTO_PAUSE",
    "SVEVoiceChange",
    "SPVISEMES",
    "SAFT48kHz16BitMono",
    "STSF_FlagCreate",
    "SPINTERFERENCE_LATENCY_WARNING",
    "SREAdaptation",
    "SVEAudioLevel",
    "SRATopLevel",
    "DISPID_SPEActualConfidence",
    "DISPID_SLPSymbolic",
    "SITooSlow",
    "DISPID_SPAsCount",
    "ISpeechWaveFormatEx",
    "DISPID_SRCreateRecoContext",
    "DISPID_SRGSetTextSelection",
    "ISpNotifySource",
    "SVEPhoneme",
    "SREStateChange",
    "SVP_16",
    "SPLO_DYNAMIC",
    "ISpRecoContext2",
    "SPWP_UNKNOWN_WORD_PRONOUNCEABLE",
    "SSTTTextBuffer",
    "DISPID_SRRTStreamTime",
    "SINoise",
    "SAFTCCITT_ALaw_11kHzMono",
    "DISPID_SRCRequestedUIType",
    "DISPID_SGRsAdd",
    "DISPID_SPRulesItem",
    "SWTAdded",
    "SPADAPTATIONRELEVANCE",
    "DISPID_SGRsDynamic",
    "ISpShortcut",
    "SGDSActive",
    "DISPID_SpeechVoice",
    "SVP_12",
    "ISpeechRecoGrammar",
    "ISpEventSource",
    "DISPID_SRCEAdaptation",
    "eLEXTYPE_PRIVATE1",
    "SpLexicon",
    "eLEXTYPE_PRIVATE17",
    "STCLocalServer",
    "DISPID_SPCLangId",
    "DISPID_SWFEFormatTag",
    "SVF_None",
    "SPSMF_SRGS_SEMANTICINTERPRETATION_W3C",
    "DISPID_SRRSetTextFeedback",
    "DISPID_SOTSetId",
    "ISpeechPhraseAlternates",
    "SPBOOKMARKOPTIONS",
    "DISPID_SRCERecognizerStateChange",
    "SVSFNLPSpeakPunc",
    "SPEI_SR_BOOKMARK",
    "ISpeechMMSysAudio",
    "DISPID_SRRTimes",
    "SPPS_Function",
    "DISPID_SPPChildren",
    "DISPID_SOTDataKey",
    "SDTLexicalForm",
    "eLEXTYPE_PRIVATE15",
    "SpCustomStream",
    "SpeechAudioFormatType",
    "SVSFParseMask",
    "ISpStreamFormat",
    "SLODynamic",
    "SPEI_ADAPTATION",
    "SPPHRASEREPLACEMENT",
    "SpeechRecognizerState",
    "STCAll",
    "ISpMMSysAudio",
    "ISpRecoGrammar2",
    "DISPID_SVResume",
    "DISPID_SVGetAudioInputs",
    "SPCS_ENABLED",
    "SPXRO_Alternates_SML",
    "DISPID_SPEsItem",
    "SVPOver",
    "SPRULE",
    "ISpVoice",
    "SAFTCCITT_uLaw_8kHzMono",
    "SAFTGSM610_8kHzMono",
    "ISpSerializeState",
    "DISPID_SpeechRecoResult",
    "DISPIDSPTSI_SelectionLength",
    "DISPID_SDKOpenKey",
    "DISPID_SRRRecoContext",
    "DISPID_SAVolume",
    "SPEI_TTS_PRIVATE",
    "DISPID_SRCEAudioLevel",
    "ISpGrammarBuilder",
    "DISPID_SVWaitUntilDone",
    "SECFNoSpecialChars",
    "DISPID_SDKGetStringValue",
    "SPEI_ACTIVE_CATEGORY_CHANGED",
    "DISPID_SRGCmdLoadFromResource",
    "SpeechLexiconType",
    "eLEXTYPE_USER",
    "eLEXTYPE_PRIVATE13",
    "DISPID_SpeechPhraseRule",
    "DISPID_SABIBufferSize",
    "SECFIgnoreWidth",
    "SPEI_HYPOTHESIS",
    "SPWORDPRONUNCIATIONLIST",
    "SVP_20",
    "DISPID_SpeechPhraseBuilder",
    "SPINTERFERENCE_TOOFAST",
    "SSTTWildcard",
    "SPAO_NONE",
    "SAFT44kHz16BitMono",
    "eLEXTYPE_PRIVATE20",
    "DISPID_SOTs_NewEnum",
    "SPPS_SuppressWord",
    "SPEI_RESERVED6",
    "ISpeechPhraseReplacements",
    "SpeechCategoryAudioOut",
    "DISPID_SVEAudioLevel",
    "SPFM_OPEN_READONLY",
    "DISPID_SVEVoiceChange",
    "SECLowConfidence",
    "DISPID_SOTCId",
    "DISPID_SPIAudioStreamPosition",
    "DISPID_SpeechGrammarRuleStateTransitions",
    "DISPID_SPRsCount",
    "SpeechDiscardType",
    "SAFTADPCM_44kHzMono",
    "DISPID_SGRSTPropertyValue",
    "SpeechStreamSeekPositionType",
    "ISpeechPhraseProperty",
    "SPTEXTSELECTIONINFO",
    "DISPID_SVSLastBookmarkId",
    "SRARoot",
    "DISPID_SPEAudioSizeBytes",
    "ISpeechRecoResultTimes",
    "SRTStandard",
    "DISPID_SVSInputWordLength",
    "SAFT11kHz16BitMono",
    "SPCONTEXTSTATE",
    "DISPID_SPRuleEngineConfidence",
    "tagSPTEXTSELECTIONINFO",
    "SREPrivate",
    "ISpPhrase",
    "DISPID_SPRuleNumberOfElements",
    "DISPID_SRCEBookmark",
    "DISPID_SASCurrentDevicePosition",
    "DISPID_SLAddPronunciationByPhoneIds",
    "eWORDTYPE_DELETED",
    "DISPID_SGRSAddSpecialTransition",
    "DISPID_SVSLastResult",
    "SRCS_Enabled",
    "SPPROPERTYINFO",
    "SWPKnownWordPronounceable",
    "SWTDeleted",
    "DISPID_SGRSAddWordTransition",
    "SDTPronunciation",
    "DISPID_SLWWord",
    "DISPID_SpeechBaseStream",
    "eLEXTYPE_PRIVATE12",
    "SPSMF_SAPI_PROPERTIES",
    "SVP_7",
    "SAFTADPCM_8kHzMono",
    "SAFTCCITT_ALaw_22kHzMono",
    "SPINTERFERENCE_NOSIGNAL",
    "SP_VISEME_17",
    "SREHypothesis",
    "SVSFPurgeBeforeSpeak",
    "SGDSInactive",
    "DISPID_SPRsItem",
    "SpeechTokenValueCLSID",
    "SPINTERFERENCE_TOOQUIET",
    "SAFT24kHz16BitStereo",
    "SAFTCCITT_uLaw_11kHzStereo",
    "SAFTCCITT_uLaw_8kHzStereo",
    "SVSFParseAutodetect",
    "Speech_Default_Weight",
    "ISpeechAudioStatus",
    "ISpeechCustomStream",
    "ISpeechRecoContext",
    "SASPause",
    "DISPID_SRGCommit",
    "SPVOICESTATUS",
    "SVP_14",
    "SP_VISEME_1",
    "SAFT24kHz16BitMono",
    "SPPHRASEPROPERTY",
    "SPVPRI_OVER",
    "SpeechPropertyNormalConfidenceThreshold",
    "DISPID_SVSLastStreamNumberQueued",
    "SVESentenceBoundary",
    "SAFTADPCM_11kHzMono",
    "SpeechUserTraining",
    "SPBO_TIME_UNITS",
    "DISPID_SVAudioOutput",
    "__MIDL_IWinTypes_0009",
    "ISpeechLexiconWord",
    "SP_VISEME_12",
    "ISpeechAudio",
    "DISPID_SPPConfidence",
    "DISPID_SVEBookmark",
    "DISPID_SpeechFileStream",
    "ISpeechXMLRecoResult",
    "DISPID_SPRuleId",
    "SRSEDone",
    "eLEXTYPE_RESERVED9",
    "ISpeechLexiconWords",
    "STSF_AppData",
    "DISPID_SVEWord",
    "SITooFast",
    "ISpeechPhraseRules",
    "SpeechTokenKeyUI",
    "SPINTERFERENCE_LATENCY_TRUNCATE_BEGIN",
    "DISPID_SPPFirstElement",
    "DISPID_SAStatus",
    "SGRSTTDictation",
    "eLEXTYPE_PRIVATE5",
    "ISpNotifyTranslator",
    "eLEXTYPE_RESERVED10",
    "SPRST_ACTIVE_ALWAYS",
    "SpMMAudioOut",
    "DISPID_SpeechLexiconPronunciation",
    "SPWORD",
    "SpWaveFormatEx",
    "DISPID_SpeechGrammarRuleStateTransition",
    "WAVEFORMATEX",
    "DISPID_SRCVoicePurgeEvent",
    "SGRSTTWildcard",
    "SAFTADPCM_22kHzMono",
    "ISpRecoGrammar",
    "SPSFunction",
    "SpPhoneConverter",
    "SpeechRecoEvents",
    "SGDSActiveUserDelimited",
    "SVP_3",
    "SPEVENT",
    "SPFM_CREATE_ALWAYS",
    "SAFT16kHz16BitStereo",
    "eLEXTYPE_VENDORLEXICON",
    "SDKLCurrentUser",
    "DISPID_SRCEventInterests",
    "SDTAll",
    "DISPID_SPRuleChildren",
    "SPWP_UNKNOWN_WORD_UNPRONOUNCEABLE",
    "SPRST_NUM_STATES",
    "DISPID_SGRSAddRuleTransition",
    "SP_VISEME_4",
    "DISPID_SRCEHypothesis",
    "SpeechMicTraining",
    "DISPID_SpeechAudioFormat",
    "SVP_21",
    "DISPID_SRAllowAudioInputFormatChangesOnNextSet",
    "DISPID_SpeechXMLRecoResult",
    "SSFMCreateForWrite",
    "DISPID_SRSClsidEngine",
    "SpPhraseInfoBuilder",
    "SSSPTRelativeToStart",
    "DISPID_SLGetPronunciations",
    "DISPID_SRRSpeakAudio",
    "DISPID_SpeechRecoResult2",
    "DISPID_SABIMinNotification",
    "SAFT22kHz16BitStereo",
    "DISPID_SVAudioOutputStream",
    "DISPID_SASetState",
    "SAFT32kHz8BitMono",
    "SRAInterpreter",
    "DISPID_SpeechMMSysAudio",
    "DISPID_SPPs_NewEnum",
]
from comtypes import _check_version

_check_version("", 1654248312.468407)
