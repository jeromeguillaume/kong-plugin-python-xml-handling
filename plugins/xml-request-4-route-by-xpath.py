#!/usr/bin/env python3
import os
import kong_pdk.pdk.kong as kong
from lxml import etree
from io import BytesIO

import sys
sys.path.append("/usr/local/kong/python/lib")

import xmlHandlingLib

Schema = (
    { "RouteToPath": {"type": "string", "required": False} },
    { "RouteToUpstream": {"type": "string", "required": False} },
    { "XPath": {"type": "string", "required": False} },
    { "XPathCondition": {"type": "string", "required": False} },
)                              
version = '1.0.0'
priority = 35
pluginName = 'xml-request-4-route-by-xpath'


#-------------------------------------------------------------------------------
# This plugin changes the Route (Upstream and/or Path) depending of XPath value
#-------------------------------------------------------------------------------
class Plugin(object):
    def __init__(self, config):
        self.config = config

    #----------------------------------------------------                                                                                                                                                                                                                                                                                                                                                                                                                   
    # Executed for every request from a client and                                                                                                                                                                                                                                                                                                                                                                                                                          
    # before it is being proxied to the upstream service                                                                                                                                                                                                                                                                                                                                                                                                                    
    #----------------------------------------------------                                                                                                                                                                                                                                                                                                                                                                                                                   
    def access(self, kong: kong.kong):
        kong.log.notice("access *** BEGIN *** | {}".format(pluginName))

        try:
            xmlH = xmlHandlingLib.XMLHandling(self.config)
    
            # Get XPath to validate condition and do dynamic routing
            XPath = ""
            XPathCondition = ""
            RouteToUpstream = ""
            RouteToPath = ""
        
            if 'XPath' in self.config:
                XPath = self.config['XPath']
            if 'XPathCondition' in self.config:
                XPathCondition = self.config['XPathCondition']
            if 'RouteToUpstream' in self.config:
                RouteToUpstream = self.config['RouteToUpstream']
            if 'RouteToPath' in self.config:
                RouteToPath = self.config['RouteToPath']
            
            xmlH.RouteByXPath(kong, True, XPath, XPathCondition, RouteToUpstream, RouteToPath)            

        except Exception as ex:                                                                                                                                                                                                                                                                                                                                                                                                                                             
            kong.log.err("XPath Routing error, exception= {}".format(ex))
            # Return a SOAP Fault to the Consumer
            xmlH.ReturnSOAPFault(kong, True, "Plugin '{}' - 'access' phase".format(pluginName), ex)
            
        kong.log.notice("access *** END *** | {}".format(pluginName))

# add below section to allow this plugin optionally be running in a dedicated process
if __name__ == "__main__":
    from kong_pdk.cli import start_dedicated_server
    start_dedicated_server(pluginName, Plugin, version, priority, Schema)