from .data_writer import DataLine


class FrameParser:
    def __init__(self):
        pass

    def parse(self, frame):
        if frame == "":
            return {}

        dataLines = {}
        for line in frame.split('\n'):
            if line:
                d = DataLine(line.strip('\r'), self.separator)
                if not self.verifyChecksum(d.tag, d.horodate, d.data, d.checksumValue):
                    raise ValueError("Wrong cheksum: %s" % d)
                dataLines[d.tag] = d

        return dataLines

    def verifyChecksum(self, tag, horodate, data, checksum):
        calculatedChecksum = self.checkSum(tag, horodate, data)

        if calculatedChecksum == checksum:
            return True

        return False

    def checkSum(self, tag, horodate, data):
        '''
         Le principe de calcul de la Checksum est le suivant :
         - calcul de la somme « S1 » de tous les caractères allant du début du champ « Etiquette »
         jusqu’au délimiteur (inclus) entre les champs « Donnée » et « Checksum ») ;
         - cette somme déduite est tronquée sur 6 bits (cette opération est faite à l’aide d’un ET logique avec 0x3F) ;
         - pour obtenir le résultat checksum, on additionne le résultat précédent S2 à 0x20.
         En résumé :
         Checksum = (S1 & 0x3F) + 0x20
         Le résultat sera toujours un caractère ASCII imprimable compris entre 0x20 et 0x5F.

         :return:
         '''
        checksum = 0

        sep = chr(self.separator)
        if horodate == "":
            line = tag + sep + data
        else:
            line = tag + sep + horodate + sep + data

        for c in line:
            checksum += ord(c)

        if self.addSeparatorInChecksum:
            checksum += self.separator

        checksum = (checksum & 0x3F) + 0x20
        return checksum


class HistoricParser(FrameParser):
    '''
    Parse historic teleinfo frame
    <LF> (0x0A) | Etiquette | <SP> (0x20) | Donnée | <SP> (0x20) | Checksum | <CR> (0x0D)
                | Zone contrôlée par le checksum   |
    '''
    startTag = 0x02
    endTag = 0x03
    separator = 0x20
    addSeparatorInChecksum = False


class LinkyParser(FrameParser):
    '''
    Parse linky (TIC v2) teleinfo frame
    STX (0x02) | Data Set | Date Set  | ... | Data Set | ETX (0x03)

    Dataset with Horodate:
    <LF> (0x0A) | Etiquette | <HT> (0x09) | Horodate | <HT> (0x09) | Donnée | <HT> (0x09) | Checksum | <CR> (0x0D)
                | Zone contrôlée par le checksum                            |

    Dataset without Horodate:
    <LF> (0x0A) | Etiquette | <HT> (0x09) | Donnée | <HT> (0x09) | Checksum | <CR> (0x0D)
                | Zone contrôlée par le checksum   |
    '''
    startTag = 0x02
    endTag = 0x03
    separator = 0x09
    addSeparatorInChecksum = True
