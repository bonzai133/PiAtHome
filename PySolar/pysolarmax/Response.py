# -*- coding: utf-8 -*-

from .MessageData import MessageData
from .MessageData import MessageDataException

import logging
logger = logging.getLogger(__name__)


# ===============================================================================
# Response
# ===============================================================================
class Response:
    def __init__(self, respData=None):
        self.messageData = None

        if respData is not None:
            self.addBlock(respData)

    def addBlock(self, respData):
        logger.debug("AddBlock: %s" % respData)

        # Parse message
        try:
            msg = MessageData()
            msg.parseMessage(respData)
        except MessageDataException as e:
            logger.error("AddBlock exception: %s" % e)
            raise

        # Concatenate messages
        if self.messageData is None:
            self.messageData = msg
        else:
            self.messageData.concatenate(msg)

    def _parseCommands(self):
        cmdList = self.messageData.payload.split(';')
        return cmdList

    def getCommands(self):
        rsp = {}

        for cmd in self._parseCommands():
            if '=' in cmd:
                cmd_array = cmd.split('=')
                key = cmd_array[0]
                value = cmd_array[1]

                rsp[key] = value.split(",")
            else:
                rsp['return'] = cmd

        # Return a dictionary with a list of values for each received command
        return rsp
