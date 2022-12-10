# -*- coding: utf-8 -*-
from MessageData import MessageData

# ===============================================================================
# Logs
# ===============================================================================
import logging
logger = logging.getLogger()


# ===============================================================================
# Request
# ===============================================================================
class Request:
    def __init__(self, cmdList, action=MessageData.GET, attr=None, fFormat=None):
        self.srcAddr = "FB"
        self.destAddr = "01"
        self.action = action

        # Check if we have a list or a single command
        if isinstance(cmdList, list):
            self.cmdList = cmdList
        else:
            self.cmdList = [cmdList]

        self.attr = attr
        self.fFormat = fFormat

    def buildRequest(self):
        '''
        Return the request string build from cmd list and parameters given in constructor.
        '''
        # Build body
        if self.action == MessageData.GET:
            # Build a GET command
            payload = ';'.join(self.cmdList)
        else:
            # Build a SET command
            if len(self.cmdList) > 1 and self.action != MessageData.GET:
                raise RequestException("Multiple commands request is only supported for GET action.")

            if self.attr is None or self.fFormat is None:
                raise RequestException("SET action require attributes and formatting function.")

            if self.fFormat:
                sFormattedAttr = self.fFormat(self.attr)
            else:
                sFormattedAttr = self.attr

            payload = "%s=%s" % (self.cmdList[0], sFormattedAttr)

        msg = MessageData(self.srcAddr, self.destAddr, self.action, payload)

        return str(msg)


class RequestException(Exception):
    pass
