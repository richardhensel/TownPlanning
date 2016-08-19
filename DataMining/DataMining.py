from xml.dom import minidom
import heapq
import sqlite3
import re

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
        self.approval                = ""
        self.addressOfSite           = ""
        self.realPropertyDescription = ""
        self.numberOfRps             = ""
        self.areaOfSite              = ""
        self.zone                    = ""
        self.nameOfWard              = ""
        self.aspectsOfDevelopment    = ""
        self.numberOfAspects         = ""
        self.descriptionOfProposal   = ""
        self.numberOfDescriptions    = ""
        self.applicant               = ""
        self.lodgementDate           = ""
        self.properlyMadeDate        = ""
        self.pre1946                 = ""
        self.stages                  = ""
        self.totalUnits              = ""

#Storage class for RP information before databasing.
class Rp:
    def __init__(self):
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.numberInApplication     = ""
        self.realPropertyType        = ""
        self.realPropertyNumber      = ""
        self.latitude                = ""
        self.longitude               = ""

class Aspect:
    def __init__(self):
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.numberInApplication     = ""
        self.aspect                  = ""

class Description:
    def __init__(self):
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.numberInApplication     = ""
        self.description             = ""
        self.numberOfUnits           = ""
        self.stage                   = ""

#Contains methods for reading an xml file and sorting into storage classes for databasing. 
class Miner:
    def __init__(self):
        # These values could be re-ordered to reduce loop times. 

        self.rpTypeList = ['BIRD.','BUP.','MAR.','GTP.','MPH.','MCP.','MSP.','NPW.','PER.']
        self.rpTypeList += ['STP.','SDP.','SPS.','SSP.','USL.','VCL.']
        self.rpTypeList += ['RP.','SL.','SP.','AP.','CP.','DP.','FP.','MP.','RL.','CG.']
        self.rpTypeList += ['B.','C.','K.','L.','M.','P.','S.','V.','W.']

        self.zoneNameList = ['lowdensity','lowmedium','mediumdensity','highdensity','character','tourist']
        self.zoneNameList += ['principalcentre','majorcentre','districtcentre','neighbourhoodcentre']
        self.zoneNameList += ['indust','enviro','conserv','community','rural','special','township']
        self.zoneNameList += ['lmr','mixeduse']


        self.aspectNameList = ['materialchangeofuse','buildingwork','reconfigure','operationalwork']

        self.descriptionNameList = ['multipledwelling','1946','reconfig', 's369']


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
                    fields.append(Field('approval', '1'))
                if 'refuse' in line.replace(' ',''):
                    fields.append(Field('approval', '0'))

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
        self.descList = []

        # Working storage for application instance. 
        application = Application()

        for field in fieldList:
            
            if 'ationreference' in field.name or 'ationnumber' in field.name:
                application.applicationReference = field.value

            elif 'approval' in field.name:
                application.approval = field.value

            elif 'doctype' in field.name:
                application.docType = field.value

            elif 'address' in field.name:
                application.addressOfSite += field.value

            # Needs to count the number of rps.
            elif 'realproperty' in field.name:
                application.numberOfRps = str(field.value.lower().count('rp'))
                application.realPropertyDescription += ',' + field.value

            elif 'area' in field.name:
                application.areaOfSite = filter(lambda x: x.isdigit(), field.value.lower().replace(' ', '').replace('m2','')) 

            elif 'zone' in field.name:
                for zoneName in self.zoneNameList:
                     
                    if zoneName in field.value.lower().replace(' ', ''):
                        application.zone = zoneName
                        break
                    # This is a bit inefficient. 
                    else:
                        application.zone = field.value
                    
            elif 'ward' in field.name:
                #some wards are multiple comma separated versions of the same name. choose only the first.
                application.nameOfWard = field.value.lower().replace(' ','').split(',')[0]

            elif 'aspects' in field.name:
                application.aspectsOfDevelopment += ',' + field.value
                # create a list of Aspects classes with the aspects contained here. 
            
            elif 'descriptionofproposal' in field.name:
                application.descriptionOfProposal += ',' + field.value

                # Check description for pre-1946 status and number of units. 
                if '1946' in field.value:
                    application.pre1946 = '1'
            

            elif 'applicant' in field.name:
                application.applicant += field.value

            elif 'lodgementdate' in field.name:
                application.lodgementDate = field.value

            elif 'properlymade' in field.name:
                application.properlyMadeDate = field.value


        # Create RP list
        rpDesc = application.realPropertyDescription
        if len(rpDesc) > 0:
            rawRpList = re.split(',|&', rpDesc)
            rpCount = 0
	    for rawRp in rawRpList:
                # pull land type and number from string. only proceed if string contains a land type. 
                rpField = self._rpNumber(rawRp)
                
                if rpField:
                    rpCount += 1
                    rpRow = Rp()

                    rpRow.applicationReference    = application.applicationReference 
                    rpRow.revisionNumber          = application.revisionNumber
                    rpRow.numberInApplication     = str(rpCount)
                    rpRow.realPropertyType        = rpField.name
                    rpRow.realPropertyNumber      = rpField.value
                    rpRow.latitude                = '123'
                    rpRow.longitude               = '456'

                    # Append current rp to list. 
                    self.rpList.append(rpRow)
        # If Rp list is empty
        else:
            self.rpList.append(Rp())

        application.numberOfRps = str(rpCount)

        aspectDesc = application.aspectsOfDevelopment
        if len(aspectDesc) > 0:
            rawAspectList = aspectDesc.lower().replace(' ','').split(',')
            aspectCount = 0
            # Compare each of the raw aspect strings to the list of posible names. 
	    for rawAspect in rawAspectList:
                for aspectName in self.aspectNameList:
                    if aspectName in rawAspect:
                        aspectCount += 1
                        aspectRow = Aspect()

                        aspectRow.applicationReference    = application.applicationReference
                        aspectRow.revisionNumber          = application.revisionNumber
                        aspectRow.numberInApplication     = str(aspectCount)
                        aspectRow.aspect                  = aspectName

                        # Append current aspect to list. 
                        self.aspectList.append(aspectRow) 
                        break
        else:
            self.aspectList.append(Aspect()) 

        application.numberOfAspects = str(aspectCount)

        descriptionDesc = application.descriptionOfProposal
        if len(descriptionDesc) > 0:

            # temporary counter of units contained within the application if in stages. 
            unitCount = 0
            # contains the current max number of units from a description section. 
            maxUnits = 0
            # Counter for stages.
            stages = 0

            rawDescriptionList = descriptionDesc.lower().replace(' ','').split(',')
            descriptionCount = 0
            # Compare each of the raw aspect strings to the list of posible names. 
	    for rawDescription in rawDescriptionList:
                for descriptionName in self.descriptionNameList:
                    if descriptionName in rawDescription:
                        descriptionCount += 1
                        descriptionRow = Description()

                        descriptionRow.applicationReference    = application.applicationReference
                        descriptionRow.revisionNumber          = application.revisionNumber
                        descriptionRow.numberInApplication     = str(descriptionCount)
                        descriptionRow.description             = descriptionName

                        #Test for stage number.
                        if 'stage' in rawDescription:
                            # First alternative. stage is a digit.
                            m = re.search("stage(([0-9]*))", rawDescription)
                            #A hack to differentiate the spelled and the numerical version of stage numbering.
                            numbers = 0
                            if m:
                                descriptionRow.stage               = m.group(1)
                                stages += 1
                                print m.group(1)
                                numbers = 1

                            # Second alternative, stage is a spelled number.
                            m = re.search("stage(one|two|three|four|five)", rawDescription)
                            if m and numbers == 0:
                                descriptionRow.stage               = m.group(1)
                                stages += 1
                                print m.group(1)

                        # test for number of units. 
                        if 'unit' in rawDescription:
                            m = re.search("([0-9]*)units", rawDescription)
                            if m:
                                descriptionRow.numberOfUnits       = m.group(1)
                                print m.group(1)

                                intUnits = int(m.group(1))

                                if maxUnits < intUnits:
                                    maxUnits = intUnits

                                #Accumulate the total number of units contained in the application.
                                if stages > 0:
                                    unitCount += intUnits

                        # Append current description to list. 
                        self.descList.append(descriptionRow) 
                        break

            # There should be at least one stage. 
            if stages == 0:
                stages += 1

            application.numberOfDescriptions = str(aspectCount)
            application.stages = str(stages)
            application.totalUnits = str(max(maxUnits, unitCount))
        else:
            self.descList.append(Description()) 

        # Add the total number of units based on the sum of stages.

        # Append the finished application onto to the list. 
        self.appList.append(application)

    # process a fragment of the rp string to pull out rp type and number.
    # Returns a single Field instance or 0, depending whether the string was valid. 
    def _rpNumber(self, rpSection):
        secContainsRp = 0
        #Compare the rpstring to the list of possible RP types.
        for rpType in self.rpTypeList:
            if rpType in str(rpSection):
                nameString = rpType
                secContainsRp = 1
                break
        
        if secContainsRp:
            valueString = ''
            reachedDot = 0 
            for char in rpSection:
                if char is '.':
                    reachedDot = 1
                elif reachedDot and char.isdigit():
                    valueString += char
            return Field(nameString, valueString)
        else:
            return 0

    def process(self, xmlPath):
        charLines = self._clusterLines(self._verticalSort(xmlPath))
        lines = self._chaListToString(charLines)
        #for line in lines:
        #    print line
        nameValueList = self._getNameValue(lines)
        #for field in nameValueList:
        #    print [field.name, field.value]

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
        s += 'approval                text,'
        s += 'addressOfSite           text,'
        s += 'realPropertyDescription text,'
        s += 'numberOfRps             text,'
        s += 'areaOfSite_m2           text,'
        s += 'zone                    text,'
        s += 'nameOfWard              text,'
        s += 'aspectsOfDevelopment    text,'
        s += 'numberOfAspects         text,'
        s += 'descriptionOfProposal   text,'
        s += 'numberOfDescriptions    text,'
        s += 'applicant               text,'
        s += 'lodgementDate           text,'
        s += 'properlyMadeDate        text,'
        s += 'pre_1946                text,'
        s += 'stages                  text,'
        s += 'totalUnits              text'
        s += ')'
        self.curs.execute(s)

        # Create RP lots table.
        s  = 'CREATE TABLE Rps ('
        s += 'applicationReference    text,'
        s += 'revisionNumber          text,'
        s += 'numberInApplication     text,'

        s += 'realPropertyType        text,'
        s += 'realPropertyNumber      text,'
        s += 'latitude                text,'
        s += 'longitude               text'
        s += ')'
        self.curs.execute(s)
  
        # Create Aspects table.
        s  = 'CREATE TABLE Aspects ('
        s += 'applicationReference    text,'
        s += 'revisionNumber          text,'
        s += 'numberInApplication     text,'

        s += 'aspect                  text'
        s += ')'
        self.curs.execute(s)

        s  = 'CREATE TABLE Descriptions ('
        s += 'applicationReference    text,'
        s += 'revisionNumber          text,'
        s += 'numberInApplication     text,'

        s += 'description             text,'
        s += 'numberOfUnits           text,'
        s += 'stage                   text'
        s += ')'
        self.curs.execute(s)


    def addRows(self, appList, rpList, aspectList, descriptionList):

        # Add to Applications table.
        for app in appList:
            s  = 'INSERT INTO Application VALUES(' 
            s += '"' + app.applicationReference    + '"' + ','
            s += '"' + app.revisionNumber          + '"' + ','
            s += '"' + app.docType                 + '"' + ','
            s += '"' + app.approval                + '"' + ','
            s += '"' + app.addressOfSite           + '"' + ','
            s += '"' + app.realPropertyDescription + '"' + ','
            s += '"' + app.numberOfRps             + '"' + ','
            s += '"' + app.areaOfSite              + '"' + ','
            s += '"' + app.zone                    + '"' + ','
            s += '"' + app.nameOfWard              + '"' + ','
            s += '"' + app.aspectsOfDevelopment    + '"' + ','
            s += '"' + app.numberOfAspects         + '"' + ','
            s += '"' + app.descriptionOfProposal   + '"' + ','
            s += '"' + app.numberOfDescriptions    + '"' + ','
            s += '"' + app.applicant               + '"' + ','
            s += '"' + app.lodgementDate           + '"' + ','
            s += '"' + app.properlyMadeDate        + '"' + ','
            s += '"' + app.pre1946                 + '"' + ','
            s += '"' + app.stages                  + '"' + ','
            s += '"' + app.totalUnits              + '"'
            s += ')'
            self.curs.execute(s)


        # Add to RP table.
        for rp in rpList:
            s  = 'INSERT INTO Rps VALUES ('
            s += '"' + rp.applicationReference    + '"' + ','
            s += '"' + rp.revisionNumber          + '"' + ','
            s += '"' + rp.numberInApplication     + '"' + ','
            s += '"' + rp.realPropertyType        + '"' + ','
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
            s += '"' + aspect.numberInApplication     + '"' + ','
            s += '"' + aspect.aspect                  + '"'
            s += ')'
            self.curs.execute(s)

        for description in descriptionList: 
            s  = 'INSERT INTO Descriptions VALUES ('
            s += '"' + description.applicationReference    + '"' + ','
            s += '"' + description.revisionNumber          + '"' + ','
            s += '"' + description.numberInApplication     + '"' + ','
            s += '"' + description.description             + '"' + ','
            s += '"' + description.numberOfUnits           + '"' + ','
            s += '"' + description.stage                   + '"'
            s += ')'
            self.curs.execute(s)

        self.conn.commit()

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    miner = Miner()
    #xmlPath = '../data/delegateDecisionA004336505.xml'
    #xmlPath = '../data/delegateDecisionA004291211.xml'
    xmlPath = '../data/delegateDecisionA004227213.xml'
    miner.process(xmlPath)

    for line in miner.appList:
        print line.zone
    for line in miner.rpList:
        print line.realPropertyNumber
    for line in miner.aspectList:
        print line.applicationReference

    #dat = Databaser('bd.db')
    #dat.addRows(miner.appList, miner.rpList, miner.aspectList, miner.descList)
