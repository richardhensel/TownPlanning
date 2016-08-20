# general functions used in scraper
import requests, bs4, time, random, selenium, csv, urllib2
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

baseAppURL = 'https://pdonline.brisbane.qld.gov.au/masterviewUI/modules/ApplicationMaster/'
baseDocURL = 'https://pdonline.brisbane.qld.gov.au/masterviewUI/modules'

#page = urllib2.urlopen('https://pdonline.brisbane.qld.gov.au/masterviewUI/modules/ApplicationMaster/default.aspx?page=found&1=thismonth&6=T')
#soup = bs4.BeautifulSoup(page, 'html.parser')

applications = []
failedApplications = []

startingURL = 'https://pdonline.brisbane.qld.gov.au/masterviewUI/modules/ApplicationMaster/default.aspx?page=found&1=01/07/2015&2=18/08/2016&3=Multiple%20Dwelling&4=&4a=&6=F&11=&12=&13=&14=&21=&22='

# Open starting page
driver = webdriver.Firefox()
driver.get(startingURL)
element = driver.find_element_by_name('ctl00$RadWindow1$C$btnOk').click()


def soupMaker():
    page = driver.page_source
    soup = bs4.BeautifulSoup(page, 'html.parser')
    return soup

def timeDelay():
    delay = random.random()*3+2
    #print 'waiting ' + str(delay) + ' seconds'
    time.sleep(delay)

def appLinkFinder(soup):
    #soupMaker()
    allLinks = soup.findAll('a')
    for link in allLinks:
        a = link.get('href')
        b = str(a)
        if 'A00' in b:
            applications.append(baseAppURL + b)
        else:
            continue

def nextPage():
    #driver = webdriver.Firefox()
    #driver.get('https://pdonline.brisbane.qld.gov.au/masterviewUI/modules/ApplicationMaster/default.aspx?page=found&1=thismonth&6=T')
    #element = driver.find_element_by_name('ctl00$RadWindow1$C$btnOk').click()
    element = driver.find_element_by_class_name('rgPageNext').click()

def delegateDecFinder(fileName):
    for application in fileName:
        try:
            print 'Next application'
            timeDelay()
            appNum = application[-10:]
            page = urllib2.urlopen(application)
            soup = bs4.BeautifulSoup(page, 'html.parser')
            docLinks = soup.findAll('a')
            for link in docLinks:
                a = link.get('title')
                b = str(a)
                if 'Delegate' in b:
                    c = baseDocURL + link.get('href')[2:]
                    timeDelay()
                    print 'found delegate decision'
                    downloadDelDecPDF(appNum + ' Delegate Decision', c)
                else:
                    failedApplications.append(appNum)
                    #print 'Could not find delegate decision'
                    continue
        except:
            print 'There was an error'
            continue

def writeToCSV(path, data):
    appLinks = open(path + '.csv', 'wb')
    wr = csv.writer(appLinks, quoting=csv.QUOTE_ALL)
    wr.writerow(data)

def downloadDelDecPDF(name,link):
    pdfsrc = urllib2.urlopen(link)
    pdfSoup = bs4.BeautifulSoup(pdfsrc, 'html.parser')
    iframe = pdfSoup.findAll('iframe')
    for link in iframe:
        reallink = link.get('src')
        reallink = str(reallink)
    f = open('../data/' + name + '.pdf', 'wb')
    f.write(urllib2.urlopen(reallink).read())
    f.close()

def openCSV(data):
    with open(data, 'rb') as f:
        reader = csv.reader(f)
        applicationList = list(reader)

def listToFile(data):
    thefile = open('failedApps.txt', 'w')
    for item in data:
        thefile.write('%s\n' % item)

x = 0

while x < 1:
    print 'making soup'
    pageHTML = soupMaker()
    print 'starting link search'
    appLinkFinder(pageHTML)
    print 'Application links found'
    timeDelay()
    print 'moving to next page'
    nextPage()
    timeDelay()
    x += 1

delegateDecFinder(applications)
listToFile(failedApplications)
print 'DONE'
