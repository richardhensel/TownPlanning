import re
from datetime import datetime
from pytz import timezone

from Databaser import Databaser, Application, Rp, Aspect, Description
from XmlParser import XmlParser, Cha


#storage class for name-value pairs before processing.
class Field:
    def __init__(self, name, value):
        self.name = name
        self.value = value

        
#Contains methods for reading an xml file and sorting into storage classes for databasing. 
# resultant data is stored as lists of Application, RP, Aspect and Description classes.  
class Miner:
    def __init__(self):
        # These values could be re-ordered to reduce loop times.
 
        # lists of expected rp, aspect, zones and descriptions.
        self.rpTypeList = ['BIRD.','BUP.','MAR.','GTP.','MPH.','MCP.','MSP.','NPW.','PER.']
        self.rpTypeList += ['STP.','SDP.','SPS.','SSP.','USL.','VCL.']
        self.rpTypeList += ['RP.','SL.','SP.','AP.','CP.','DP.','FP.','MP.','RL.','CG.']
        self.rpTypeList += ['B.','C.','K.','L.','M.','P.','S.','V.','W.']

        self.zoneNameList = ['lowdensity','lowmedium','mediumdensity','highdensity','character','tourist']
        self.zoneNameList += ['principalcentre','majorcentre','districtcentre','neighbourhoodcentre']
        self.zoneNameList += ['indust','enviro','conserv','community','rural','special','township']
        self.zoneNameList += ['lmr','mixeduse']

        
        self.aspectNameList = ['materialchangeofuse','buildingwork','reconfigure','operationalwork']

        self.descriptionNameList = ['multipledwelling','1946','reconfig', 's369', 'dwellinghouse']

        # datetime object representing the zero of unix time.
        self.unixZero = timezone('UTC').localize(datetime(1970,1,1))

    # reads strings, identifies if a 
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
                    fields.append(Field('decision', 'approve'))
                if 'refuse' in line.replace(' ',''):
                    fields.append(Field('decision', 'refuse'))
                if 'amend' in line.replace(' ',''):
                    fields.append(Field('decision', 'amend'))
                if 'concurrence' in line.replace(' ',''):
                    fields.append(Field('decision', 'concurrence'))

            lineCount += 1

        ## append multiple instances of the same field. 
        finalFields = []
        for field1 in fields:
            for field2 in fields:
                if field1.name == field2.name and field1.value != field2.value:
                    finalFields.append(Field(field1.name, field1.value + ',' + field2.value))
                    

        return fields


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

            elif 'decision' in field.name:
                application.decision = field.value

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
                m = re.search("([0-9]{2})([a-zA-Z]+)([0-9]{4})", field.value.replace(' ', ''))

                if m:
                    # https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
                    date = timezone('Australia/Brisbane').localize(datetime.strptime(m.group(1)+m.group(2)+m.group(3) + '12', '%d%B%Y%H'))

                    application.lodgementDate = m.group(1) + ' ' + m.group(2) + ' ' + m.group(3)
                    application.lodgementUnix = str(int((date - self.unixZero).total_seconds()))
                else:
                    application.lodgementDate = field.value

            elif 'properlymade' in field.name:
                m = re.search("([0-9]{2})([a-zA-Z]+)([0-9]{4})", field.value.replace(' ', ''))

                if m:
                    date = timezone('Australia/Brisbane').localize(datetime.strptime(m.group(1)+m.group(2)+m.group(3) + '12', '%d%B%Y%H'))

                    application.properlyMadeDate = m.group(1) + ' ' + m.group(2) + ' ' + m.group(3)
                    application.properlyMadeUnix = str(int((date - self.unixZero).total_seconds()))
                else:
                    application.properlyMadeDate = field.value 
                
                #print application.properlyMadeDate
                #print timezone('Australia/Brisbane').localize(datetime.fromtimestamp(int(application.properlyMadeUnix)))


        # Create RP list
        rpDesc = application.realPropertyDescription
        if len(rpDesc) > 0:
            # Split the rp string on a comma or anpersand character. 
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

            application.numberOfRps = str(rpCount)
        # If Rp list is empty
        else:
            self.rpList.append(Rp())


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

            application.numberOfAspects = str(aspectCount)
        else:
            self.aspectList.append(Aspect()) 


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
                            # string has all spelled numbers converted to integers before testing with regex.
                            m = re.search("stage(([0-9]*))", self._al2num(rawDescription))

                            if m:
                                descriptionRow.stage               = m.group(1)
                                stages += 1

                        # test for number of units. 
                        if 'unit' in rawDescription:
                            m = re.search("([0-9]*)units", rawDescription)
                            if m:
                                descriptionRow.numberOfUnits       = m.group(1)

                                intUnits = int(m.group(1))
                                #Update running maximum of units in description
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

    # replaces spelled numbers with integers.
    def _al2num(self, string):
        string = string.replace('one', '1')
        string = string.replace('two', '2')
        string = string.replace('three', '3')
        string = string.replace('four', '4')
        string = string.replace('five', '5')
        string = string.replace('six', '6')
        string = string.replace('seven', '7')
        string = string.replace('eight', '8')
        string = string.replace('nine', '9')
        string = string.replace('ten', '10')
        return string

    def process(self, lineStrings):
        #for line in lineStrings:
        #    print line
        nameValueList = self._getNameValue(lineStrings)
        #for field in nameValueList:
        #    print [field.name, field.value]

        self._processApplication(nameValueList)


if __name__ == "__main__":
    xmlParser = XmlParser()
    miner = Miner()
    #xmlPath = '../data/delegateDecisionA004336505.xml'
    #xmlPath = '../data/delegateDecisionA004291211.xml'
    #xmlPath = '../data/delegateDecisionA004227213.xml'
    #xmlPath = '../data/delegateDecisionA004232447.xml'
    xmlPath = '../data/xml/A004190766DelegateDecision.xml'
    xmlParser.parse(xmlPath)
    lineStrings = xmlParser.returnStrings()
    for line in lineStrings:
        print line

    miner.process( lineStrings )

    for line in miner.appList:
        print line.zone
    for line in miner.rpList:
        print line.realPropertyNumber
    for line in miner.aspectList:
        print line.applicationReference

    #dat = Databaser('bd.db')
    #dat.addRows(miner.appList, miner.rpList, miner.aspectList, miner.descList)
