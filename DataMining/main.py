import glob, os
import subprocess


from Databaser import Databaser, Application, Rp, Aspect, Description
from XmlParser import XmlParser, Cha
from DataMining import Miner, Field


if __name__ == "__main__":
    wd = str(os.getcwd())
    
    miner = Miner()
    xmlParser = XmlParser()
    dat = Databaser('bd.db')

    dataDir = '../data/'
    os.chdir(dataDir)

    for file in glob.glob("*.pdf"):

        pdfPath = dataDir + str(file)
        xmlPath = pdfPath.replace('.pdf', '.xml')

        # Run the pdf to xml converter
        #bashCommand = wd + '/pdf2txt.py -o ' + xmlPath + ' ' + pdfPath
        #process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        #output = process.communicate()[0]
        #print output

        xmlParser.parse(xmlPath)
        miner.process( xmlParser.returnStrings() )
        print miner.appList[0].applicationReference
    
        dat.addRows(miner.appList, miner.rpList, miner.aspectList, miner.descList)

        ## Remove the xml file afterwards.
        #bashCommand = 'rm ' +  xmlPath
        #process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        #output = process.communicate()[0]
        #print output

    dat.close()
