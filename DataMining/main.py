import glob, os
import subprocess


from Databaser import Databaser, Application, Rp, Aspect, Description
from XmlParser import XmlParser, Cha
from Miner import Miner, Field

def convertToXml():
    
    pdfDir = wd + '/../data/pdf/'
    os.chdir(pdfDir)

    # Delete all pdf files less than 1k in size. 
    bashCommand = 'find . -name "*.pdf" -size -1000c -delete'
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]

    for file in glob.glob("*.pdf"):

        pdfPath = pdfDir + str(file)
        xmlPath = pdfPath.replace('/pdf/','/xml/').replace('.pdf', '.xml')

        print xmlPath
        # Run the pdf to xml converter
        bashCommand = wd + '/pdf2txt.py -o ' + xmlPath + ' ' + pdfPath
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        #print output


def mine():
    miner = Miner()
    xmlParser = XmlParser()
    dat = Databaser('bd.db')


    xmlDir = wd + '/../data/xml/'
    os.chdir(xmlDir)

    # Delete all xml files less than 1k in size. 
    bashCommand = 'find . -name "*.xml" -size -1000c -delete'
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]

    # Mine that shit.
    for file in glob.glob("*.xml"):
        xmlPath = xmlDir + str(file)
        print xmlPath
        xmlParser.parse(xmlPath)
        miner.process( xmlParser.returnStrings() )
        print miner.appList[0].applicationReference
    
        dat.addRows(miner.appList, miner.rpList, miner.aspectList, miner.descList)

    dat.close()

if __name__ == "__main__":
    # The location of the main python file. 
    wd = str(os.getcwd())
    
    #convertToXml()
    mine()

