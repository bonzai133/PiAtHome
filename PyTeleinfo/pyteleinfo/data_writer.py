import logging
from json import JSONEncoder
import json


class DataLineEncoder(JSONEncoder):
    def default(self, object):
        if isinstance(object, DataLine):
            return object.toJson()
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return json.JSONEncoder.default(self, object)


class DataLine:
    def __init__(self, line, separator):
        self.line = line
        self.separator = separator

        self.tag = ""
        self.horodate = ""
        self.data = ""
        self.checksumValue = ""

        self._parse()

    def __str__(self):
        return self.toJson()

    def __repr__(self):
        return "%s: %s|%s|%s" % (self.tag, self.horodate, self.data, self.checksumValue)

    def toJson(self):
        if self.horodate != "" and self.data != "":
            return self.horodate + '|' + self.data
        elif self.horodate != "":
            return self.horodate

        return self.data

    def _parse(self):
        group = self.line.split(chr(self.separator))

        if len(group) == 3:
            (tag, data, checksum) = group
            horodate = ""
        elif len(group) == 4:
            (tag, horodate, data, checksum) = group
        else:
            raise ValueError("Wrong line format: %s" % group)

        if len(checksum) != 1:
            raise ValueError("Wrong checksum length: %s" % group)

        self.tag = tag
        self.horodate = horodate
        self.data = data
        self.checksumValue = ord(checksum)


class DataWriter:
    def __init__(self, filenamePrefix):
        self.filenamePrefix = filenamePrefix

    def write(self, dataLines):
        filename = ''
        if 'ADCO' in list(dataLines.keys()):
            filename = self.filenamePrefix + dataLines['ADCO'].data
        elif 'ADSC' in list(dataLines.keys()):
            filename = self.filenamePrefix + dataLines['ADSC'].data
        else:
            logging.debug("ADCO or ADSC not found in data: %s" % list(dataLines.keys()))
            raise KeyError("Can't find counter key in data")

        logging.debug("Will write to file %s" % filename)
        with open(filename, 'w') as fp:
            json.dump(dataLines, fp, cls=DataLineEncoder)
