import glob, os
import subprocess

from DataMining import Cha
from DataMining import Field
from DataMining import Application
from DataMining import Rp
from DataMining import Aspect
from DataMining import Miner
from DataMining import Databaser

if __name__ == "__main__":
    wd = str(os.getcwd())
    
    miner = Miner()
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

        miner.process(xmlPath)
        print miner.appList[0].applicationReference
    
        dat.addRows(miner.appList, miner.rpList, miner.aspectList, miner.descList)

        ## Remove the xml file afterwards.
        #bashCommand = 'rm ' +  xmlPath
        #process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        #output = process.communicate()[0]
        #print output

    dat.close()
