""" 
    simplerobotparser.py

    A simple(r) robots.txt parser.
    It implements Crawl-Delay and Request-Rate directives, and you can easily
    expand it to do more. If you are interested, look for the comment:
    "special functions -- you may want to extend this part"
    
    See example of usage at the end.

    This implementation follow the guidelines of 
    http://www.w3.org/TR/html4/appendix/notes.html#h-B.4.1.1
    http://www.robotstxt.org/
    http://en.wikipedia.org/wiki/Robots.txt
    and more.

    ***
    Author: Balint Vekredy
    This work is licensed under the GNU GPLv3 license.
    For details please see:
    http://www.gnu.org/licenses/quick-guide-gplv3.html
    ***
    
"""
# TODO: proper documentation
# TODO: check meta tags of html 
# TODO: add implementation of SiteMap directive.
# http://en.wikipedia.org/wiki/Robots.txt#Sitemap 
import urllib

__all__ = ['RobotFileParser', '']
class RobotFileParser:
    """
    A ParseError will be raised in every case when a badly formed robots.txt 
    file causes the algorithms of RobotFileParser to fail.
    """
            
    def __init__(self):
        self.useragents = {}
        
    def __str__(self):
        return '\n\n'.join([str(ua) for ua in self.useragents])
    
    def fetchUrl(self, url):
        opener = urllib.FancyURLopener()
        self.robotfile = opener.open(url)

    def fetchLocal(self, filename):
        """ 
        Opens @filename.
        """
        self.robotfile = open(filename)

    def parse(self):
        """
        Parses a robots.txt file 
        Must call fetchLocal or fetchUrl first
        """
        ua = None
        for line in self.robotfile.read().split('\n'):
            if line.strip():
                data = line.split(':')
                if len(data) != 2:
                    raise ParseError('Unexpected data format of robots.txt')
                lineType = data[0].strip().lower()
                lineContent = data[1].strip()
                
                if lineType == "user-agent":
                    try:
                        ua = self.useragents[lineContent]
                    except KeyError:
                        #if the user agent mentioned for the first time, add it
                        self.useragents[lineContent] = UserAgent(lineContent)
                        ua = self.useragents[lineContent]
                else:
                    if ua is None:
                        raise ParseError("Rule precedes User-Agent definition")
                    ua.rules.append((lineType,lineContent))                    
    
    def getUserAgents(self):
        return [ua.name for ua in self.useragents.values()]
    
    def getProperty(self, agent, lineType):
        """ 
        Returns all of @agent's @lineType rules
        e.g.:
        getProperty('*','disallow') returns something like:
        ['/secret', '/dontlikerobots']
        
        Return values: 
        List of the rule's contents or None if the user agent is not present
        """ 
        try: 
            return [v for (k,v) in self.useragents[agent].rules \
                    if k == lineType.lower()]
        except KeyError:
            return None
    
    def isAllowed(self, agent, url):
        
        if agent not in self.getUserAgents():
            if agent != '*':
                return self.isAllowed('*',url)
            else:
                # if there are no rules for this User-agent and no rules for
                # '*', then we are allowed to crawl
                return True
        disallow = [1 for d in self.getProperty(agent, 'disallow') if url.startswith(d)]
        allow = [1 for a in self.getProperty(agent, 'allow') if url.startswith(a)]
        if (len(allow)):
            return True
        elif (len(disallow)):
            return False
        return True
    
    """ special functions -- you may want to extend this part """
       
    def getCrawlDelay(self,agent):
        """
        Returns the Craw-Delay for @agent in seconds (int), 
        or None if not defined
        """
        cd = self.getProperty(agent,'crawl-delay')
        if cd is None or len(cd) == 0:
            return None
        else:
            # disregard any but the first occurance
            return int(cd[0])
        
    def getRequestRate(self,agent):
        """
        Returns the Request-rate for @agent in request/seconds (float), 
        or None if not defined
        """
        rr = self.getProperty(agent,'request-rate')
        if rr is None or len(rr) == 0:
            return None
        else:
            # disregard any but the first occurance
            try:
                (r,s) = rr[0].split('/')
                return float(r)/float(s)
            except ValueError:
                raise ParseError('Invalid value for Request-rate for ' + agent)
               
class UserAgent:
    
    def __init__(self,name):
        self.name = name
        self.rules = []

    def __str__(self):
        return self.name + '\n' + '\n'.join([str(r[0]) + ': ' + str(r[1]) \
                                   for r in self.rules])


class ParseError(Exception):

    def __init__(self, msg):
        self.msg = msg

class RobotExclusion:
    """
    This class wraps the RobotFileParser class
    
    Usage:
    r = RobotExclusion(url,agent) #create instance, parses url, sets agent
    r.isAllowed(url)              #checks whether the agent is allowed on that
                                  #url
    r.crawldelay                  #crawl-delay value for agent. Default: None
    r.requestrate                 #request-rate value for agent. Default: None
    
    """
    def __init__(self, robotsUrl, agent):
        self.url = robotsUrl
        self.agent = agent
        self.__parseRobot()
        
    def __parseRobot(self):
        self.rp = RobotFileParser()
        self.rp.fetchUrl(self.url)
        self.rp.parse()
        self.crawldelay = self.rp.getCrawlDelay(self.agent)
        self.requestrate = self.rp.getRequestRate(self.agent)
    
    def isAllowed(self,url):
        return self.rp.isAllowed(self.agent, url) 
    
if __name__ == "__main__":
    r = RobotFileParser()
    r.fetchLocal('robots.txt')
    r.parse() 
    agent = '*'
    print r.isAllowed(agent,'/path/of/interest')
    print r.getCrawlDelay(agent)
    print r.getRequestRate(agent)
