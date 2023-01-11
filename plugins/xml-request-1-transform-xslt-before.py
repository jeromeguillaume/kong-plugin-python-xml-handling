#!/usr/bin/env python3
import os
import kong_pdk.pdk.kong as kong
from lxml import etree
from io import BytesIO

import sys
sys.path.append("/usr/local/kong/python/lib")

import xmlHandlingLib

Schema = (
    { "xsltTransform": {"type": "string", "required": False} },
)

version = '1.0.0'
priority = 50
pluginName = 'xml-request-1-transform-xslt-before'


#-----------------------------------------------------------------
# This plugin transforms the XML content of the request with XSLT
#-----------------------------------------------------------------
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

            # Get XSLT value from property plugin
            xsltTransform = ""
            if 'xsltTransform' in self.config:
                xsltTransform = self.config['xsltTransform']
            
            # Transform XML with XSLT Transformation
            xmlH.XSLTransform(kong, True, xsltTransform)

        except Exception as ex:
            kong.log.err("XML Handling error, exception= {}".format(ex))
            # Return a SOAP Fault to the Consumer
            xmlH.ReturnSOAPFault(kong, True, "Plugin '{}' - 'access' phase".format(pluginName), ex)

        kong.log.notice("access *** END *** | {}".format(pluginName))

# add below section to allow this plugin optionally be running in a dedicated process
if __name__ == "__main__":
    from kong_pdk.cli import start_dedicated_server
    start_dedicated_server(pluginName, Plugin, version, priority, Schema)