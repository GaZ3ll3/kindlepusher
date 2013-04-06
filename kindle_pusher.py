# -*- coding: utf-8 -*-
"""
Created on Fri Apr 05 19:36:24 2013

@author: lurker
"""
import requests
import re
#import time
#uncomment for debug the timing test
import os
import getpass
import smtplib
from HTMLParser import HTMLParser
from re import sub
from sys import stderr
from traceback import print_exc
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders


class _DeHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + ' ')

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.__text.append('\n\n')
        elif tag == 'br':
            self.__text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.__text.append('\n\n')

    def text(self):
        return ''.join(self.__text).strip()


def dehtml(text):
    try:
        parser = _DeHTMLParser()
        parser.feed(text)
        parser.close()
        return parser.text()
    except:
        print_exc(file=stderr)
        return text

def getlinks():
    url = 'http://www.statesman.com/s/business/'
    business = 'http://www.statesman.com/news/business/'
    response = requests.get(url)
    html = response.content
    addresses = []
    # store the addresses
    locate_start=[m.start() for m in re.finditer(business, html)]
    for begins in range(len(locate_start)):
        ends = html.find('>',locate_start[begins])
        #the <a href...> ends
        address = html[locate_start[begins]:ends-1]
        addresses.append(address)
        
    return list(set(addresses))

def crawl():
    #this function crawls the content of the links
    addresses = getlinks()
    news = []
    for m in range(len(addresses)):
        readin = addresses[m]
        #print readin
        body = requests.get(readin).content
        content = dehtml(body).decode("utf-8").encode("ascii","ignore")
        # date
        Time_Title_begin = content.find("Posted:")
        Time_Title_end = content.find("var",Time_Title_begin)
        Time_Title = content[Time_Title_begin:Time_Title_end]
        #print Time_Title
        #Author
        Author_begin = content.find("By", Time_Title_end)
        if content[Author_begin+3].isupper():
            #check if it is a person's name or organization
            Author_end = content.find("\n", Author_begin)
            Author = content[Author_begin:Author_end]
        else:
            Author_begin = content.find("\n", Time_Title_end)
            Author_end = content.find("\n",Author_end)
        #print Author
        
        Passage_begin = Author_end
        Passage_end = content.find("var switchTo5x=false",Passage_begin)
        Passage = content[Passage_begin:Passage_end]
        #print passage
        bundle = Time_Title, Author,Passage
        news.append(bundle)
    return news
            
def pump(news,filename):
    #news = crawl()
    fp = open(filename, 'w')
    fp.write('\n'.join('%s \n %s \n %s \n' % piece for piece in news))
    # TODO: remove articles before 7 days ago.
    # TODO: build up database for each article, using SHA-1 or SHA-2 as identity
    fp.close()
        

def mail(gmail_user, gmail_pwd, to, subject, text, attach):
   msg = MIMEMultipart()

   msg['From'] = gmail_user
   msg['To'] = to
   msg['Subject'] = subject

   msg.attach(MIMEText(text))

   part = MIMEBase('application', 'octet-stream')
   part.set_payload(open(attach, 'rb').read())
   Encoders.encode_base64(part)
   part.add_header('Content-Disposition',
           'attachment; filename="%s"' % os.path.basename(attach))
   msg.attach(part)

   mailServer = smtplib.SMTP("smtp.gmail.com", 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(gmail_user, gmail_pwd)
   mailServer.sendmail(gmail_user, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
   mailServer.close()


def main():
    gmail_user = raw_input('Gmail Account: ')
    gmail_pwd  = getpass.getpass()
    kindle_user = raw_input('Kindle Email: ')
    news = crawl()
    pump(news, "business_news.txt")
    #send to myself
    
    mail(gmail_user,gmail_pwd, kindle_user,"","","business_news.txt")

        
if __name__ == '__main__':
    main()
