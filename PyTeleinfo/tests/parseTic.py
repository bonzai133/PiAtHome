#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class DataLine:
    '''
     0x0A Tag 0x09 Horodate 0x09 value 0x09 Checksum 0x0D

     0x0A Tag 0x09 value 0x09 Checksum 0x0D

    '''
    def __init__(self, data=b''):
        self.tag = ''
        self.horodate = ''
        self.value = ''
        self.checksum = 0

        self.raw = data

        self._parse()

    def _parse(self):
        logging.debug("Parse %s", self.raw)
        groups = self.raw.split(b'\t')

        if len(groups) == 3:
            logging.debug("Line without Horodate")
            self.tag = groups[0].decode('ascii')
            self.value = groups[1].decode('ascii')
            self.checksum = ord(groups[2])
        elif len(groups) == 4:
            logging.debug("Line with Horodate")
            self.tag = groups[0].decode('ascii')
            self.horodate = groups[1].decode('ascii')
            self.value = groups[2].decode('ascii')
            self.checksum = ord(groups[3])
        else:
            logging.warning("Wrong line format")

    def verifyChecksum(self):
        if self.checksum == self.calculateChecksum():
            return True

        return False

    def calculateChecksum(self):
        checksum = 0
        for c in self.raw[:-1]:
            checksum += c

        checksum = (checksum & 0x3F) + 0x20
        return checksum


def main():
    filename = 'tic_std1.txt'

    logging.info("Start")

    infoLines = {}
    with open(filename, 'rb') as fi:
        start = False
        for line in fi:
            if 0x02 in line:
                if not start:
                    start = True
                    continue
                else:
                    break

            if 0x03 in line:
                start = False
                break

            if start:
                line = line.strip(b'\n')
                if line != b'':
                    dataLine = DataLine(line)
                    if not dataLine.verifyChecksum():
                        logging.warning("Wrong checksum")

                    if dataLine.horodate != '':
                        infoLines[dataLine.tag] = dataLine.horodate + '|' + dataLine.value
                    else:
                        infoLines[dataLine.tag] = dataLine.value

    print(infoLines)


if __name__ == "__main__":
    main()
