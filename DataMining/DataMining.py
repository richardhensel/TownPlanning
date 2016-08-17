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
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.docType                 = ""
        self.decision                = ""
        self.addressOfSite           = ""
        self.realPropertyDescription = ""
        self.numberOfRps             = ""
        self.areaOfSite              = ""
        self.zone                    = ""
        self.nameOfWard              = ""
        self.aspectsOfDevelopment    = ""
        self.descriptionOfProposal   = ""
        self.applicant               = ""
        self.lodgementDate           = ""
        self.properlyMadeDate        = ""

#Storage class for RP information before databasing.
class Rp:
    def __init__(self):
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.numberInApplication     = ""
        self.realPropertyNumber      = ""
        self.latitude                = ""
        self.longitude               = ""

class Aspect:
    def __init__(self):
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.realPropertyNumber      = ""
        self.latitude                = ""
        self.longitude               = ""


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
            if 'DECISION' in line.replace(' ','') or 'ECISIO' in line.replace(' ',''):

                if 'DELEGATE' in line.replace(' ',''):
                    fields.append(Field('doctype', 'delegate'))
                    print 'delegate'
                    print [fields[-1].name, fields[-1].value]

                #print 'Decision'
                decisionStringCount += 1

                if decisionStringCount == 1:
                    documentZone = 'details'
                elif decisionStringCount == 2:
                    documentZone = 'reasons'
                continue

            if 'anddirectthat' in line.replace(' ','').lower():
                documentZone = 'directions'

            if documentZone == 'details':
                if 'SUBMISSION' in line or 'SITE:' in line or 'APPLICATION:' in line:
                    continue
                #print 'in details zone'

                # sort lines into name-containing and non-name-containing
                # colon indicates whether a line contains a name. 
                #test if the next column contains a field name and if it is unique.  
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
                    fields.append(Field(nameInLine.lower().replace(' ',''), valueInLine.strip()))
                        
                else:
                    # If a line does not contain a colon, it is part of the value from the 
                    # previous field.
                    # append line to previous entry.
                    if len(fields) > 0 and 'doctype' not in fields[-1].name:
                        fields[-1].value += ' ' + line.strip()

            if documentZone == 'reasons':
                if 'approve' in line.replace(' ',''):
                    fields.append(Field('decision', 'approve'))
                if 'refuse' in line.replace(' ',''):
                    fields.append(Field('decision', 'refuse'))

            lineCount += 1

        ## append multiple instances of the same field. 
        finalFields = []
        for field1 in fields:
            for field2 in fields:
                if field1.name == field2.name and field1.value != field2.value:
                    finalFields.append(Field(field1.name, field1.value + ',' + field2.value))
                    

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
        # Create a list for each table to be modified. 
        self.appList = []
        self.rpList = []
        self.aspectList = []

        # Working storage for application instance. 
        application = Application()


        for field in fieldList:
            if 'ationreference' in field.name or 'ationnumber' in field.name:
                application.applicationReference = field.value

            elif 'decision' in field.name:
                application.decision = field.value

            elif 'doctype' in field.name:
                application.docType = field.value

            elif 'address' in field.name:
                application.addressOfSite += field.value

            # Needs to count the number of rps.
            elif 'realproperty' in field.name:
                application.numberOfRps = str(field.value.lower().count('rp'))
                application.realPropertyDescription = field.value

		rpList = field.value.split(",")
		
            elif 'area' in field.name:
                application.areaOfSite = field.value.lower().replace(' ', '')

            elif 'zone' in field.name:
                if 'lowmedium' in field.value.lower().replace(' ', ''):
                    application.zone = 'LOWMEDIUM'
                else:
                    application.zone = 'ERROR'

            elif 'ward' in field.name:
                application.nameOfWard = field.value.lower().replace(' ','')

            elif 'aspects' in field.name:
                application.aspectsOfDevelopment += field.value
                # create a list of Aspects classes with the aspects contained here. 
            
            elif 'descriptionofproposal' in field.name:
                application.descriptionOfProposal += field.value

            elif 'applicant' in field.name:
                application.applicant += field.value

            elif 'lodgementdate' in field.name:
                application.lodgementDate = field.value

            elif 'properlymade' in field.name:
                application.properlyMadeDate = field.value

        application.revisionNumber = str(1)
        self.appList.append(application)

        # Create RP list
        if rpList:
            rpCount = 1
	    for rawRp in rpList:
                rpRow = Rp()
                rpRow.applicationReference    = self.appList[-1].applicationReference 
                rpRow.revisionNumber          = '1'
                rpRow.numberInApplication     = str(rpCount)
                rpRow.realPropertyNumber      = ''.join(c for c in rawRp if c.isdigit())
                # ^^ This test for integfers is flawed. other numbers can get in
                rpRow.latitude                = '123'
                rpRow.longitude               = '456'

                self.rpList.append(rpRow)
                rpCount += 1
        # If Rp list is empty
        else:
            self.rpList.append(Rp())

        # Create Aspects list
        #aspectsCount = 1
        #for    
        self.aspectList.append(Aspect()) 

    def _processRp(self, rpString):
        secContainsRp = 0
        for section in rpString.split(','):
            if 'RP.' in section:
                
                for char in section:
                    

    def process(self, xmlPath):
        charLines = self._clusterLines(self._verticalSort(xmlPath))
        lines = self._chaListToString(charLines)

        nameValueList = self._getNameValue(lines)
        print len(nameValueList)
        for field in nameValueList:
            print [field.name, field.value]

        self._processApplication(nameValueList)

        #return nameValueList        

class Databaser:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.curs = self.conn.cursor()

        try:
            self.createTables() 
        except:
            print 'error creating tables, maybe already exists...'

    def createTables(self):
        # Create Delegate Decisions table.
        s  = 'CREATE TABLE Application ('
        s += 'applicationReference    text,'
        s += 'revisionNumber          text,'
        s += 'docType                 text,'
        s += 'decision                text,'
        s += 'addressOfSite           text,'
        s += 'realPropertyDescription text,'
        s += 'numberOfRps             text,'
        s += 'areaOfSite_m2           text,'
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
        s  = 'CREATE TABLE Rps ('
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

    def addRows(self, appList, rpList, aspectList):

        # Add to Applications table.
        for app in appList:
            s  = 'INSERT INTO Application VALUES(' 
            s += '"' + app.applicationReference    + '"' + ','
            s += '"' + app.revisionNumber          + '"' + ','
            s += '"' + app.docType                 + '"' + ','
            s += '"' + app.decision                + '"' + ','
            s += '"' + app.addressOfSite           + '"' + ','
            s += '"' + app.realPropertyDescription + '"' + ','
            s += '"' + app.numberOfRps             + '"' + ','
            s += '"' + app.areaOfSite              + '"' + ','
            s += '"' + app.zone                    + '"' + ','
            s += '"' + app.nameOfWard              + '"' + ','
            s += '"' + app.aspectsOfDevelopment    + '"' + ','
            s += '"' + app.descriptionOfProposal   + '"' + ','
            s += '"' + app.applicant               + '"' + ','
            s += '"' + app.lodgementDate           + '"' + ','
            s += '"' + app.properlyMadeDate        + '"' 
            s += ')'
            self.curs.execute(s)


        # Add to RP table.
        for rp in rpList:
            s  = 'INSERT INTO Rps VALUES ('
            s += '"' + rp.applicationReference    + '"' + ','
            s += '"' + rp.revisionNumber          + '"' + ','
            s += '"' + rp.numberInApplication     + '"' + ','
            s += '"' + rp.realPropertyNumber      + '"' + ','
            s += '"' + rp.latitude                + '"' + ','
            s += '"' + rp.longitude               + '"' 
            s += ')'
            self.curs.execute(s)

        # Add to Aspects table.
        for aspect in aspectList: 
            s  = 'INSERT INTO Aspects VALUES ('
            s += '"' + aspect.applicationReference    + '"' + ','
            s += '"' + aspect.revisionNumber          + '"' + ','
            s += '"' + aspect.realPropertyNumber      + '"' + ','
            s += '"' + aspect.latitude                + '"' + ','
            s += '"' + aspect.longitude               + '"' 
            s += ')'
            self.curs.execute(s)

        self.conn.commit()

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    miner = Miner()
    xmlPath = '../data/delegateDecisionA004336505.xml'
    miner.process(xmlPath)

    for line in miner.appList:
        print line.zone
    for line in miner.rpList:
        print line.realPropertyNumber
    for line in miner.aspectList:
        print line.applicationReference

    dat = Databaser('bd.db')
    dat.addRows(miner.appList, miner.rpList, miner.aspectList)
