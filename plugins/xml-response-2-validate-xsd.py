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
priority = 25
pluginName = 'xml-response-2-validate-xsd'


#---------------------------------------------------------------------------
# This plugin checks the validity the XML content of the response with XSLT
# #-------------------------------------------------------------------------
class Plugin(object):
    def __init__(self, config):
        self.config = config

    def access(self, kong: kong.kong):
        kong.log.notice("access *** BEGIN *** | {}".format(pluginName))
        kong.service.request.enable_buffering()
        kong.log.notice("access *** END *** | {}".format(pluginName))
    
    #------------------------------------------------------------------------------------------------------------------
    # Executed for each chunk of the response body received from the upstream service.
    # Since the response is streamed back to the client, it can exceed the buffer size and be streamed chunk by chunk.
    # This function can be called multiple times
    #------------------------------------------------------------------------------------------------------------------
    def response(self, kong: kong.kong):
        kong.log.notice("response *** BEGIN *** | {}".format(pluginName))
        
        try:
            xmlH = xmlHandlingLib.XMLHandling(self.config)
            
            # Get XSD SOAP schema from the plugin configuration
            xsdSoapSchema = ""
            if 'xsdSoapSchema' in self.config:
                xsdSoapSchema = self.config['xsdSoapSchema']
            
            #  Validate XML against API XSD schema
            xmlH.XMLValidateWithXSD(kong, False, xsdSoapSchema, "")
            
            # Get XSD SOAP schema from the plugin configuration
            xsdApiSchema = ""
            if 'xsdApiSchema' in self.config:
                xsdApiSchema = self.config['xsdApiSchema']
            
            #  Validate XML against API XSD schema
            xmlH.XMLValidateWithXSD(kong, False, "", xsdApiSchema)
            
        except Exception as ex:
            kong.log.err("XML Handling error, exception= {}".format(ex))
            # Return a SOAP Fault to the Consumer
            xmlH.ReturnSOAPFault(kong, False, "Plugin '{}' - 'response' phase".format(pluginName), ex)

        kong.log.notice("response *** END *** | {}".format(pluginName))

# add below section to allow this plugin optionally be running in a dedicated process
if __name__ == "__main__":
    from kong_pdk.cli import start_dedicated_server
    start_dedicated_server(pluginName, Plugin, version, priority, Schema)