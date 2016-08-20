
import heapq
from xml.dom import minidom



# Class for individual characters coming from XML.
class Cha:
    def __init__(self, pageNum, charId, startX, startY, size, value):
        self.pageNum = pageNum
        self.charId = charId
        self.startX = startX
        self.startY = startY
        self.size = size
        self.value = value


class XmlParser:

    # parses an xml file, stores a list of list of Cha elements, sorted by line. 
    def parse(self, xmlPath):
        xmldoc = minidom.parse(xmlPath)
        charList = xmldoc.getElementsByTagName('text')
        
        self.charLineList = self._clusterLines( self._verticalSort( charList ) )

    def returnStrings(self):
        return self._chaListToString( self.charLineList )

    def returnChars(self):
        return self.charLineList

    #Parse the xml document, returning a list of Char objects ordered from top to bottom on page.
    def _verticalSort(self, charList):
        charStack = []
        charId = 0
        for cha in charList:
            # Determine which page the character is located in.
            parent = cha
            while True:
                # Ascent the parent tree until page is reached.
                parent = parent.parentNode
                if parent.nodeName == 'page':
                    pageNum = int(parent.getAttribute('id'))
                    pageCoords = parent.getAttribute('bbox').split(",")
                    pageYOffset = pageNum * float(pageCoords[3])
                    break 

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
                    x = charStack[-1].startX + 4.9 # 4.9 is roughly the distance between chars
                    y = charStack[-1].startY 
                    size = charStack[-1].size

                else:
                    x = 0
                    y = 0 
                    size = 0
            charStack.append(Cha(pageNum, charId, x, y, size, nodeVal))
            charId += 1

        return heapq.nsmallest(len(charStack), charStack, key = lambda p: p.startY)

    # Take a list of Char objects, sort into individual lines. 
    # Resurns a list of lists of Char objects, ordered by line. 
    def _clusterLines(self, charList, lineOffset = 5):
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

    def _chaListToString(self, charListList):
        stringLine = ''
        stringList = []
        for line in charListList:
            for char in line:
                stringLine += char.value
            stringList.append(stringLine)
            stringLine = ''
        return stringList
