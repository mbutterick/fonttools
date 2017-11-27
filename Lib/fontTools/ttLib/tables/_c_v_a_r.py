from __future__ import \
    print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from . import DefaultTable
from fontTools.misc import sstruct
from fontTools.ttLib.tables.TupleVariation import \
    compileTupleVariationStore, decompileTupleVariationStore, TupleVariation


# https://www.microsoft.com/typography/otspec/cvar.htm
# https://www.microsoft.com/typography/otspec/otvarcommonformats.htm
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6cvar.html

CVAR_HEADER_FORMAT = """
    > # big endian
    majorVersion:        H
    minorVersion:        H
    tupleVariationCount: H
    offsetToData:        H
"""

CVAR_HEADER_SIZE = sstruct.calcsize(CVAR_HEADER_FORMAT)


class table__c_v_a_r(DefaultTable.DefaultTable):
    dependencies = ["cvt ", "fvar"]

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.majorVersion, self.minorVersion = 1, 0
        self.variations = []

    def compile(self, ttFont, useSharedPoints=False):
        tupleVariationCount, tuples, data = compileTupleVariationStore(
            variations=[v for v in self.variations if v.hasImpact()],
            pointCount=len(ttFont["cvt "].values),
            axisTags=[axis.axisTag for axis in ttFont["fvar"].axes],
            sharedTupleIndices={},
            useSharedPoints=useSharedPoints)
        header = {
            "majorVersion": self.majorVersion,
            "minorVersion": self.minorVersion,
            "tupleVariationCount": tupleVariationCount,
            "offsetToData": CVAR_HEADER_SIZE + len(tuples),
        }
        return bytesjoin([
            sstruct.pack(CVAR_HEADER_FORMAT, header),
            tuples,
            data
        ])

    def decompile(self, data, ttFont):
        axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]
        header = {}
        sstruct.unpack(CVAR_HEADER_FORMAT, data[0:CVAR_HEADER_SIZE], header)
        self.majorVersion = header["majorVersion"]
        self.minorVersion = header["minorVersion"]
        assert self.majorVersion == 1, self.majorVersion
        self.variations = decompileTupleVariationStore(
            tableTag=self.tableTag, axisTags=axisTags,
            tupleVariationCount=header["tupleVariationCount"],
            pointCount=len(ttFont["cvt "].values), sharedTuples=None,
            data=data, pos=CVAR_HEADER_SIZE, dataPos=header["offsetToData"])

    def fromXML(self, name, attrs, content, ttFont):
        if name == "version":
            self.majorVersion = int(attrs.get("major", "1"))
            self.minorVersion = int(attrs.get("minor", "0"))
        elif name == "tuple":
            valueCount = len(ttFont["cvt "].values)
            var = TupleVariation({}, [None] * valueCount)
            self.variations.append(var)
            for tupleElement in content:
                if isinstance(tupleElement, tuple):
                    tupleName, tupleAttrs, tupleContent = tupleElement
                    var.fromXML(tupleName, tupleAttrs, tupleContent)

    def toXML(self, writer, ttFont, progress=None):
        axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]
        writer.simpletag("version",
                         major=self.majorVersion, minor=self.minorVersion)
        writer.newline()
        for var in self.variations:
            var.toXML(writer, axisTags)
