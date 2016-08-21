import sqlite3

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
        self.lodgementUnix           = ""
        self.properlyMadeDate        = ""
        self.properlyMadeUnix        = ""
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

#Storage class for Aspect information before databasing.
class Aspect:
    def __init__(self):
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.numberInApplication     = ""
        self.aspect                  = ""

#Storage class for Description information before databasing.
class Description:
    def __init__(self):
        self.applicationReference    = ""
        self.revisionNumber          = ""
        self.numberInApplication     = ""
        self.description             = ""
        self.numberOfUnits           = ""
        self.stage                   = ""


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
        s += 'lodgementUnix           text,'
        s += 'properlyMadeDate        text,'
        s += 'properlyMadeUnix        text,'
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
            s += '"' + app.lodgementUnix           + '"' + ','
            s += '"' + app.properlyMadeDate        + '"' + ','
            s += '"' + app.properlyMadeUnix        + '"' + ','
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
