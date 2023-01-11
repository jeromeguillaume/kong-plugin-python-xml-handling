#!/usr/bin/env python3
import os
import kong_pdk.pdk.kong as kong
from lxml import etree
from io import BytesIO

import sys
sys.path.append("/usr/local/kong/python/lib")

import xmlHandlingLib

Schema = (
     { "xsdSoapSchema": {"type": "string", "default": xmlHandlingLib.XSD_SCHEMA_SOAP, "required": False} },
     { "xsdApiSchema": {"type": "string", "required": False} },
)

version = '1.0.0'
priority = 45
pluginName = 'xml-request-2-validate-xsd'


#--------------------------------------------------------------------
# This plugin checks the validity the XML content of the request with XSLT
# #--------------------------------------------------------------------
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
            
            # Get SOAP XSD shema from the plugin configuration
            xsdSoapSchema = ""
            if 'xsdSoapSchema' in self.config:
                xsdSoapSchema = self.config['xsdSoapSchema']
            
            #  Validate XML against SOAP XSD schema
            xmlH.XMLValidateWithXSD(kong, True, xsdSoapSchema, "")
            
            # Get API XSD shema from the plugin configuration
            xsdApiSchema = ""
            if 'xsdApiSchema' in self.config:
                xsdApiSchema = self.config['xsdApiSchema']
            
            #  Validate XML against API XSD schema
            xmlH.XMLValidateWithXSD(kong, True, "", xsdApiSchema)
            
        except Exception as ex:
            kong.log.err("XML Handling error, exception= {}".format(ex))
            # Return a SOAP Fault to the Consumer
            xmlH.ReturnSOAPFault(kong, True, "Plugin '{}' - 'access' phase".format(pluginName), ex)

        kong.log.notice("access *** END *** | {}".format(pluginName))

# add below section to allow this plugin optionally be running in a dedicated process
if __name__ == "__main__":
    from kong_pdk.cli import start_dedicated_server
    start_dedicated_server(pluginName, Plugin, version, priority, Schema)