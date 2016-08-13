from xml.dom import minidom
import heapq
import sqlite3

# Class for individual characters coming from XML.

class Cha:
    def __init__(self, pageNum, charId, startX, startY, size, value):
        self.pageNum = pageNum
        self.charId = charId
        self.startX = startX
        self.startY = startY
        self.size = size
        self.value = value

#storage class for name-value pairs before processing.
class Field:
    def __init__(self, name, value):
        self.name = name
        self.value = value

#Storage class for Application information before databasing.
class Application:
    def __init__(self):
        self.applicationReference    = None
        self.revisionNumber          = None
        self.docType                 = None
        self.decision                = None
        self.addressOfSite           = None
        self.realPropertyDescription = None
        self.numberOfRps             = None
        self.areaOfSite              = None
        self.zone                    = None
        self.nameOfWard              = None
        self.aspectsOfDevelopment    = None
        self.descriptionOfProposal   = None
        self.applicant               = None
        self.lodgementDate           = None
        self.properlyMadeDate        = None

#Storage class for RP information before databasing.
class Rp:
    def __init__(self):
        self.applicationReference    = None
        self.revisionNumber          = None
        self.numberInApplication     = None
        self.realPropertyNumber      = None
        self.latitude                = None
        self.longitude               = None

class Aspect:
    def __init__(self):
        self.applicationReference    = None
        self.revisionNumber          = None
        self.realPropertyNumber      = None
        self.latitude                = None
        self.longitude               = None


#Contains methods for reading an xml file and sorting into storage classes for databasing. 
class Miner:

    def _verticalSort(self, xmlPath = 'exml.xml'):
        xmldoc = minidom.parse(xmlPath)
        
        charList = xmldoc.getElementsByTagName('text')
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

                if 'DELEGATE' in line:
                    fields.append(Field('doctype', 'delegate'))

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

                    # Strings are converted to lower case and have spaces removed. 
                    fields.append(Field(nameInLine.lower().replace(' ',''), valueInLine.lower().strip()))
                    
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

    def _processApplication(self, fieldList):
        application = Application()
        for field in fieldList:
            if 'reference' in field.name:
                application.applicationReference = field.value

            elif 'decision' in field.name:
                application.decision = field.value

            elif 'doctype' in field.name:
                application.docType = field.value

            elif 'address' in field.name:
                application.addresssOfSite = field.value

            # Needs to count the number of rps.
            elif 'realproperty' in field.name:
                application.numberOfRps = field.value.lower().count('rp') 
                

                rpList = field.value


            elif 'area' in field.name:
                application.areaOfSite = field.value

            elif 'zone' in field.name:
                if 'lowmedium' in field.value:
                    application.zone = 'LOWMEDIUM'
                else
                    application.zone = 'ERROR'

            elif 'ward' in field.name:
                application.nameOfWard = field.value

            elif 'aspects' in field.name:
                application.aspectsOfDevelopment = field.value
                # create a list of Aspects classes with the aspects contained here. 
            
            elif 'descriptionofproposal' in field.name:
                application.descriptionOfProposal = field.value

            elif 'applicant' in field.name:
                application.applicant = field.value

            elif 'lodgementdate' in field.name:
                application.lodgementDate = field.value

            elif 'properlymade' in field.name:
                application.properlyMadeDate = field.value

            application.revisionNumber = 1

['docType', 'delegate']
['Address of Site', '12 WILTON TCE YERONGA QLD 4104']
['Real Property Description', 'L5 RP.59813']
['Area of Site', '607 m2']
['Zone', 'LOW MEDIUM DENSITY RESIDENTIAL (2 OR 3 STOREY MIX) ZONE']
['Name of Ward', 'Tennyson']
['Aspects of Development', 'DA - SPA - Material Change of Use - Development Permit']
['Description of Proposal', 'Multiple Dwellings']
['Applicant', 'Ken and Susan Poggiolic/- Hillocc Pty LtdPO Box 886COORPAROO  QLD 4151']
['Application Reference', 'A003974498']
['Lodgement Date', '01 October 2014']
['Properly Made Date', '10 October 2014']
['decision', 'refuse']


    def output(self, xmlPath):
        charLines = self._clusterLines(self._verticalSort(xmlPath))

        nameValueList = self._getNameValue(self._chaListToString(charLines))
        return nameValueList        

class Databaser:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.curs = self.conn.cursor()


    def createTables(self):
        print "Creating Tables..."
        # Create Delegate Decisions table.
        s  = 'CREATE TABLE Application ('
        s += 'applicationReference    text,'
        s += 'revisionNumber          text,'
        s += 'docType                 text,'
        s += 'decision                text,'
        s += 'addressOfSite           text,'
        s += 'realPropertyDescription text,'
        s += 'numberOfRps             text,'
        s += 'areaOfSite              text,'
        s += 'zone                    text,'
        s += 'nameOfWard              text,'
        s += 'aspectsOfDevelopment    text,'
        s += 'descriptionOfProposal   text,'
        s += 'applicant               text,'
        s += 'lodgementDate           text,'
        s += 'properlyMadeDate        text'
        s += ')'
        self.curs.execute(s)

        # Create RP lots table.
        s  = 'CREATE TABLE RPs ('
        s += 'applicationReference    text,'
        s += 'revisionNumber          text,'
        s += 'numberInApplication     text,'
        s += 'realPropertyNumber      text,'
        s += 'latitude                text,'
        s += 'longitude               text'
        s += ')'
        self.curs.execute(s)
  
        # Create Aspects table.
        s  = 'CREATE TABLE Aspects ('
        s += 'applicationReference    text,'
        s += 'revisionNumber          text,'
        s += 'realPropertyNumber      text,'
        s += 'latitude                text,'
        s += 'longitude               text'
        s += ')'
        self.curs.execute(s)

    #def addApplicationLine(self, ):
    


 
if __name__ == "__main__":
    miner = Miner()
    xmlPath = 'exml.xml'
    nameValueList = miner.output(xmlPath)

    for field in nameValueList:
        print [field.name, field.value]
    dat = Databaser('bd.db')
    dat.createTables()
