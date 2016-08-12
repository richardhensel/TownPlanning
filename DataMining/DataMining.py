from xml.dom import minidom
import heapq

class Cha:
    def __init__(self, pageNum, charId, startX, startY, size, value):
        self.pageNum = pageNum
        self.charId = charId
        self.startX = startX
        self.startY = startY
        self.size = size
        self.value = value

class Field:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Miner:

    def _verticalSort(self, xmlPath = 'exml.xml'):
        xmldoc = minidom.parse(xmlPath)
        
        charList = xmldoc.getElementsByTagName('text')
        charStack = []
        charId = 0
        for cha in charList:
            #for i in range(0,10):
            #cha = charList[i]
            parent = cha
            while True:
                # Ascent the parent tree until page is reached.
                #print 'pass through'
                parent = parent.parentNode
                if parent.nodeName == 'page':
                    #print 'parent is page'
                    pageNum = int(parent.getAttribute('id'))
                    pageCoords = parent.getAttribute('bbox').split(",")
                    pageYOffset = pageNum * float(pageCoords[3])
                    #print 'offset', pageYOffset
                    break 

            #print cha.getAttribute('bbox')
            #print [cha.childNodes[0].nodeValue, 'end']
            try:
                nodeVal = str(cha.childNodes[0].nodeValue)
                #print 'good char'
            except:
                #print 'non-Recognised char'
                nodeVal = '-'


            try:
                coords = cha.getAttribute('bbox').split(",")

                size = float(cha.getAttribute('size'))

                x = int(float(coords[0]))
                y = int(pageYOffset - int(float(coords[3]))) 
                #print 'good params'

                
            except:
                #print 'No params'

                if nodeVal == '\n':
                    continue

                if len(charStack) > 0:
                    x = charStack[-1].startX + 4.9
                    y = charStack[-1].startY 
                    size = charStack[-1].size

                else:
                    x = 0
                    y = 0 
                    size = 0
            charStack.append(Cha(pageNum, charId, x, y, size, nodeVal))
            charId += 1

        return heapq.nsmallest(len(charStack), charStack, key = lambda p: p.startY)

    def _clusterLines(self, charList, lineOffset = 3):
        lineList = [] #list of lineout lists
        line = [] #list of Cha objects
        for i in range(1,len(charList)-1):
            currentChar = charList[i]
            prevChar = charList[i-1]
            if abs(currentChar.startY - prevChar.startY) < lineOffset:
                line.append(currentChar)
            else:
                line = heapq.nsmallest(len(line), line, key = lambda l: l.startX)
                lineList.append(line)
                line = []
                line.append(currentChar)

        return lineList


    def _getNameValue(self, lineList):
        fields = []
        lineCount = 0
        decisionStringCount = 0
        submissionStringCount = 0
        documentZone = ''
        for line in lineList:
            #print line
            if 'DECISION' in line:
                #print 'Decision'
                decisionStringCount += 1

                if decisionStringCount == 1:
                    documentZone = 'details'
                elif decisionStringCount == 2:
                    documentZone = 'reasons'
                continue

            if 'And Direct That' in line:
                documentZone = 'directions'

            if documentZone == 'details':
                if 'SUBMISSION' in line or 'SITE:' in line or 'APPLICATION:' in line:
                    continue
                #print 'in details zone'

                # sort lines into name-containing and non-name-containing
                # colon indicates whether a line contains a name. 
                if ':' in line:
                    nameInLine = ''
                    valueInLine = ''
                    reachedColon = False
                    for char in line:
                        if char == ':':
                            reachedColon = True
                            continue
                        # value is everything in the line after reachedcolon
                        if not reachedColon:
                            nameInLine += char
                        # name is everyting before reachedcolon
                        else:
                            valueInLine += char

                    # Create a new entry in the fields list.
                    # name is everything before a semicolon
                    # Value is everything after the semicolon.
                    fields.append(Field(nameInLine.strip(), valueInLine.strip()))
                    
                else:
                    # If a line does not contain a colon, it is part of the value from the 
                    # previous field.
                    # append line to previous entry.
                    if len(fields) > 0 : 
                        fields[-1].value += line.strip()

            if documentZone == 'reasons':
                if 'approve' in line:
                    fields.append(Field('decision', 'approve'))
                if 'refuse' in line:
                    fields.append(Field('decision', 'refuse'))

            lineCount += 1
        return fields

    def _chaListToString(self, charList):
        stringLine = ''
        stringList = []
        for line in charList:
            for char in line:
                stringLine += char.value
            stringList.append(stringLine)
            stringLine = ''
        return stringList
        

    def output(self, xmlPath):
        charLines = self._clusterLines(self._verticalSort(xmlPath))

        nameValueList = self._getNameValue(self._chaListToString(charLines))
        return nameValueList        

class Databaser:
    def __init__(self, path):
        self.path = path

 
if __name__ == "__main__":
    miner = Miner()
    xmlPath = 'exml.xml'
    nameValueList = miner.output(xmlPath)

    for field in nameValueList:
        print [field.name, field.value]
