# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)


# ===============================================================================
# MessageData
# ===============================================================================
class MessageData:
    GET = "64"
    SET = "C8"

    def __init__(self, srcAddr='', destAddr='', action=GET, payload=''):
        self.srcAddr = srcAddr
        self.destAddr = destAddr
        self.action = action
        self.payload = payload

    def parseMessage(self, respData):
        if not respData.startswith('{') or (not respData.endswith('}') and not respData.endswith(')')):
            logger.debug("Missing brackets around message data")
            raise MessageDataException("Missing brackets around message data")

        # Remove brackets and split message
        respData = respData[1:-1]
        msgParts = respData.split("|")

        if len(msgParts) != 3:
            logger.debug("Can't split message data")
            raise MessageDataException("Can't split message data")

        header = msgParts[0]
        body = msgParts[1]
        checksum = int(msgParts[2], 16)

        # Split body
        if ':' in body:
            bodyParts = body.split(':')
            if len(bodyParts) != 2:
                logger.debug("Can't split body data")
                raise MessageDataException("Can't split body data")

            self.action = bodyParts[0]
            self.payload = bodyParts[1]
        else:
            # Continuation body, we don't have the action
            self.action = None
            self.payload = body

        # Split header
        headerParts = header.split(";")

        if len(headerParts) != 3:
            logger.debug("Can't split message header")
            raise MessageDataException("Can't split message header")

        self.srcAddr = headerParts[0]
        self.destAddr = headerParts[1]
        msgLen = int(headerParts[2], 16)

        self._verifyLength(msgLen)

        self._verifyChecksum(checksum)

    def __str__(self):
        if self.action is not None:
            return '{%s;%s;%02X|%s:%s|%04X}' % (self.srcAddr, self.destAddr, self.calculateLength(),
                                                self.action, self.payload, self.calculateChecksum())
        else:
            return '{%s;%s;%02X|%s|%04X}' % (self.srcAddr, self.destAddr, self.calculateLength(),
                                             self.payload, self.calculateChecksum())

    @staticmethod
    def _checkSum16(sText):
        '''Calculate the cheksum 16 of the given argument'''
        # Convert string to char array
        cArray = list(sText)
        iSum = 0
        for c in cArray:
            iSum += ord(c)
            iSum %= 2 ** 16

        return iSum

    def calculateChecksum(self):
        if self.action is not None:
            msg = "%s;%s;%02X|%s:%s|" % (self.srcAddr, self.destAddr, self.calculateLength(), self.action, self.payload)
        else:
            msg = "%s;%s;%02X|%s|" % (self.srcAddr, self.destAddr, self.calculateLength(), self.payload)

        checksum = MessageData._checkSum16(msg)
        return checksum

    def calculateLength(self):
        if self.action is not None:
            totalLen = len("{00;00;00|00:|0000}") + len(self.payload)
        else:
            totalLen = len("{00;00;00||0000}") + len(self.payload)

        return totalLen

    def _verifyLength(self, givenLen):
        expectedLen = self.calculateLength()

        if givenLen != expectedLen:
            logger.debug("Invalid length in message data. Given length '%d'; expected length '%d'." % (givenLen, expectedLen))
            raise MessageDataException("Invalid Length")

    def _verifyChecksum(self, givenChecksum):
        expectedChecksum = self.calculateChecksum()

        if givenChecksum != expectedChecksum:
            logger.debug("Invalid checksum in message data. Given checksum '%d'; expected checksum '%d'." % (givenChecksum, expectedChecksum))
            raise MessageDataException("Invalid checksum")

    def concatenate(self, msgData):
        if not isinstance(msgData, MessageData):
            raise MessageDataException("msgData is not an instance of MessageData")

        if self.srcAddr != msgData.srcAddr or self.destAddr != msgData.destAddr:
            raise MessageDataException("Source or destination address mismatch")

        if self.action is not None and msgData.action is not None and self.action != msgData.action:
            raise MessageDataException("Direction mismatch")

        self.payload += msgData.payload


# ===============================================================================
# MyException
# ===============================================================================
class MessageDataException(Exception):
    pass
