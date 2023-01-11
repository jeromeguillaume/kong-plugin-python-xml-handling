#!/usr/bin/env python3

from lxml import etree
import kong_pdk.pdk.kong as kong
from io import BytesIO

# Default Content-Type
DEFAULT_CONTENT_TYPE = "text/xml; charset=utf-8"

# Default Begin of SOAP Enveope Response
DEFAULT_SOAP_ENVELOPE_BEGIN = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"

# Header name
HEADER_RESPONSE_1_TRANSFORM_XLT = "x-xml-response-1-transform-xslt"

# XSD schema to verify SOAP envelope validity
XSD_SCHEMA_SOAP ='''
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:tns="http://schemas.xmlsoap.org/soap/envelope/"
           targetNamespace="http://schemas.xmlsoap.org/soap/envelope/" >
  <!-- Envelope, header and body -->
  <xs:element name="Envelope" type="tns:Envelope" />
  <xs:complexType name="Envelope" >
    <xs:sequence>
      <xs:element ref="tns:Header" minOccurs="0" />
      <xs:element ref="tns:Body" minOccurs="1" />
      <xs:any namespace="##other" minOccurs="0" maxOccurs="unbounded" processContents="lax" />
    </xs:sequence>
    <xs:anyAttribute namespace="##other" processContents="lax" />
  </xs:complexType>

  <xs:element name="Header" type="tns:Header" />
  <xs:complexType name="Header" >
    <xs:sequence>
      <xs:any namespace="##other" minOccurs="0" maxOccurs="unbounded" processContents="lax" />
    </xs:sequence>
    <xs:anyAttribute namespace="##other" processContents="lax" />
  </xs:complexType>
  
  <xs:element name="Body" type="tns:Body" />
  <xs:complexType name="Body" >
    <xs:sequence>
      <xs:any namespace="##any" minOccurs="0" maxOccurs="unbounded" processContents="lax" />
    </xs:sequence>
    <xs:anyAttribute namespace="##any" processContents="lax" >
	  <xs:annotation>
	    <xs:documentation>
		  Prose in the spec does not specify that attributes are allowed on the Body element
		</xs:documentation>
	  </xs:annotation>
	</xs:anyAttribute>
  </xs:complexType>

       
  <!-- Global Attributes.  The following attributes are intended to be usable via qualified attribute names on any complex type referencing them.  -->
  <xs:attribute name="mustUnderstand" >	
     <xs:simpleType>
     <xs:restriction base='xs:boolean'>
	   <xs:pattern value='0|1' />
	 </xs:restriction>
   </xs:simpleType>
  </xs:attribute>
  <xs:attribute name="actor" type="xs:anyURI" />

  <xs:simpleType name="encodingStyle" >
    <xs:annotation>
	  <xs:documentation>
	    'encodingStyle' indicates any canonicalization conventions followed in the contents of the containing element.  For example, the value 'http://schemas.xmlsoap.org/soap/encoding/' indicates the pattern described in SOAP specification
	  </xs:documentation>
	</xs:annotation>
    <xs:list itemType="xs:anyURI" />
  </xs:simpleType>

  <xs:attribute name="encodingStyle" type="tns:encodingStyle" />
  <xs:attributeGroup name="encodingStyle" >
    <xs:attribute ref="tns:encodingStyle" />
  </xs:attributeGroup>

  <xs:element name="Fault" type="tns:Fault" />
  <xs:complexType name="Fault" final="extension" >
    <xs:annotation>
	  <xs:documentation>
	    Fault reporting structure
	  </xs:documentation>
	</xs:annotation>
    <xs:sequence>
      <xs:element name="faultcode" type="xs:QName" />
      <xs:element name="faultstring" type="xs:string" />
      <xs:element name="faultactor" type="xs:anyURI" minOccurs="0" />
      <xs:element name="detail" type="tns:detail" minOccurs="0" />      
    </xs:sequence>
  </xs:complexType>

  <xs:complexType name="detail">
    <xs:sequence>
      <xs:any namespace="##any" minOccurs="0" maxOccurs="unbounded" processContents="lax" />
    </xs:sequence>
    <xs:anyAttribute namespace="##any" processContents="lax" /> 
  </xs:complexType>

</xs:schema>
'''

class XMLHandling:
    def __init__(self, config):
        self.config = config

    #-------------------------------------
    # Return a SOAP Fault to the Consumer
    #-------------------------------------
    def ReturnSOAPFault(self, kong, request, ErrMsg, ErrEx):
        # If we are in Response context (and not Request)
        if request == False:
          try:  
            # Clear the Reponse Header
            kong.response.clear_header(HEADER_RESPONSE_1_TRANSFORM_XLT)
          except Exception as ex:
              pass

        msgError = DEFAULT_SOAP_ENVELOPE_BEGIN + """
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <soap:Fault>
      <faultcode>soap:Client</faultcode>
      <faultstring>{}: {}</faultstring>
      <detail/>
    </soap:Fault>
  </soap:Body>
</soap:Envelope>
        """.format(ErrMsg, ErrEx)
        dictType = {"Content-Type": DEFAULT_CONTENT_TYPE}

        # Don't call the backend API and send back to Consumer a SOAP Error Message
        return kong.response.exit(500, msgError, dictType)
        
    #-------------------------------------
    # Transform the XML content with XSLT
    #-------------------------------------
    def XSLTransform (self, kong, request, xsltTransform):
        kong.log.notice("XSLTransform *** BEGIN ***")
        kong.log.notice("request=", request)
        
        # If there is no XSLT configuration we do nothing
        if xsltTransform == "":
            kong.log.notice("No XSLT transformation is configured, so there is nothing to do")
            return

        # Get XML SOAP envelope from consumer's Request
        soapEnvelope = ""
        try:
            # If we extract SOAP body from the Request
            if request == True:
                soapEnvelope = kong.request.get_raw_body()
            # Else we extract SOAP body from the Response
            else:
                # Get Header (optionally set before by 'xml-response-1-transform-xslt' plugin)
                headerXMLResponse_1 = kong.response.get_header(HEADER_RESPONSE_1_TRANSFORM_XLT)
                
                # If the Header exists we get SOAP Envelope from the Header
                if headerXMLResponse_1:
                    soapEnvelope = headerXMLResponse_1.replace('%0A', '\r').encode('utf-8')
                # Else we get the SOAP Envelope from the Reponse Body
                else:
                    soapEnvelope = kong.service.response.get_raw_body()
        except Exception as ex:
            kong.log.err("Unable to get raw body, exception={}".format(ex))
            # Return a SOAP Fault to the Consumer
            self.ReturnSOAPFault(kong, request, "XSLT Transformation failed", ex)
            
        kong.log.notice("BEFORE XSLT transform, body= ", soapEnvelope)
        try: 
            # Construct the XSLT transformer
            xslt_root = etree.XML(xsltTransform)
            transform = etree.XSLT(xslt_root)

            # Run the transformation on the XML SOAP envelope
            doc = etree.parse(BytesIO(soapEnvelope))
            result_tree = transform(doc)
            
            # Remove empty Namepace added by the 'lxml' library (xmlns="")
            result_tree_no_empty_xmlns = etree.tostring(result_tree, pretty_print=True).replace(b' xmlns=""', b'')
            
            # Change the Consumer request with the new XST transformed values
            kong.log.notice("AFTER XSLT transform, body=", result_tree_no_empty_xmlns)
            
            # If we handle SOAP body in the Request we change the Body of request
            if request == True:
                kong.service.request.set_raw_body (result_tree_no_empty_xmlns)
            # Else we handle SOAP body in the Response we add an HTTP header in the response
            # and the last plugin executed (which handles the response) does a 'kong.response.exit' by
            # seeting a Reponsse body
            else:
                # Remove the current Header
                kong.response.clear_header(HEADER_RESPONSE_1_TRANSFORM_XLT)
                # Add new value to the Header
                kong.response.add_header(HEADER_RESPONSE_1_TRANSFORM_XLT, result_tree_no_empty_xmlns)
                
        except Exception as ex:
            kong.log.err("XSLT Transformation, exception={}".format(ex))
            # Return a SOAP Fault to the Consumer
            self.ReturnSOAPFault(kong, request, "XSLT Transformation failed", ex)
        
        kong.log.notice("XSLTransform *** END ***")

    #--------------------------------------------------------------------
    # Validate XML against XSD schema
    # SOAP schema and API schema are given in parameters
    #--------------------------------------------------------------------
    def XMLValidateWithXSD (self, kong, request, xsdSoapSchema, xsdApiSchema):
        kong.log.notice("XML Validate XSD *** BEGIN ***")
        soapEnvelope = ""
        tree = ""
        
        kong.log.notice("request=", request)
        try:
            # If we handle the XML Request
            if request == True:
                soapEnvelope = kong.request.get_raw_body()
            # Else we handle the XML Response
            else:
                # Get Header (optionally set before by 'xml-response-1-transform-xslt' plugin)
                headerXMLResponse_1 = kong.response.get_header(HEADER_RESPONSE_1_TRANSFORM_XLT)
                
                # If the Header exists we get SOAP Envelope from the Header
                if headerXMLResponse_1 and len(headerXMLResponse_1) > 0:
                    soapEnvelope = headerXMLResponse_1.replace('%0A', '\r').encode('utf-8')
                # Else we get the SOAP Envelope from the Reponse Body
                else:
                    soapEnvelope = kong.service.response.get_raw_body()
        except Exception as ex:
            kong.log.err("Unable to get raw body from request or response, exception=", "%s" % (ex))
            # Return a SOAP Fault to the Consumer
            self.ReturnSOAPFault(kong, request, "XSD validation failed", ex)
            
        kong.log.notice("XMLValidate body= ", soapEnvelope)
        
        # If we have a Body content, we check the validity of SOAP envelope against its XSD schema
        if soapEnvelope != "" and xsdSoapSchema != "":
            try:
                kong.log.notice("Check SOAP Envelope XML against its XSD schema")

                # Load the SOAP envelope XSD schema
                schema_root_soap = etree.XML (xsdSoapSchema)
                schema_root_soap_etree = etree.XMLSchema(schema_root_soap)
                parse_root_soap = etree.XMLParser(schema = schema_root_soap_etree)
                
                # Parse the SOAP envelope (retrieved from request) against the schema
                tree = etree.parse(BytesIO(soapEnvelope), parse_root_soap)
            except Exception as ex:
                kong.log.err("Unable check the validity of SOAP envelope against its XSD schema, exception=", "%s" % (ex))
                # Return a SOAP Fault to the Consumer
                self.ReturnSOAPFault(kong, request, "XSD validation failed", ex)
              
        # If we have a Body content, we check the validity of <soap:Body> content against its XSD schema
        if soapEnvelope != "" and xsdApiSchema != "":
            try:
                kong.log.notice("Check API XML against its XSD schema")
                if tree == "":
                    tree = etree.parse(BytesIO(soapEnvelope))

                # Load the API XSD schema
                schema_api = etree.XML(xsdApiSchema)
                schema_api_etree = etree.XMLSchema(schema_api)
                parser_api = etree.XMLParser(schema = schema_api_etree)

                # Get <soap:Body> content from entire <soap:Envelope>
                #
                # Example:
                # <soap:Envelope xmlns:xsi=....">
                #   <soap:Body>
                #     <Add xmlns="http://tempuri.org/">
                #       <a>5</a>
                #       <b>7</b>
                #     </Add>
                #   </soap:Body>
                # </soap:Envelope>
                root = tree.getroot()

                # root.getchildren()[0] => <soap:Body>...</soap:Body>
                # root.getchildren()[0].getchildren()[0] => <Add ...</Add>
                bodySOAPContent = root.getchildren()[0].getchildren()[0]
                kong.log.notice("etree.tostring(bodySOAPContent=", etree.tostring(bodySOAPContent))
                
                # Parse the SOAP envelope (retrieved from request) agains the schema
                tree = etree.parse(BytesIO(etree.tostring(bodySOAPContent)), parser_api)
            except Exception as ex:
                kong.log.err("Unable check the validity of API content against its XSD schema, exception=", "%s" % (ex))
                # Return a SOAP Fault to the Consumer
                self.ReturnSOAPFault(kong, request, "XSD validation failed", ex)
                
        kong.log.notice("XML Validate XSD *** END ***")

    #------------------------------------------------------------------
    # Change the Route (Upstream and/or Path) depending of XPath value
    #------------------------------------------------------------------
    def RouteByXPath (self, kong, request, XPath, XPathCondition, RouteToUpstream, RouteToPath):
        kong.log.notice("XPathRouting *** BEGIN ***")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
        # If we don't have the same number of parameters of 'XPathReplace' and 'XPathReplaceValue' we return an Error
        if XPath == "" or XPathCondition == "" or RouteToUpstream == "":
            kong.log.notice("No routing rule configured, so there is nothing to do")
            return                                                                                                                                                                                                                                                                                                                                                                                                                

        soapEnvelope = ""
        try:
            soapEnvelope = kong.request.get_raw_body()
            kong.log.notice("SOAP body=", soapEnvelope)

            treeSOAP = etree.parse(BytesIO(soapEnvelope))
            rootSOAP = treeSOAP.getroot()

            XpathValue = rootSOAP.find(XPath.strip()).text
            kong.log.notice("XPath value compared : ", XpathValue)
            if XpathValue == XPathCondition:
                kong.log.notice("Condition validated")
                kong.service.set_upstream(RouteToUpstream)
                
                if RouteToPath != "":
                    kong.service.request.set_path(RouteToPath)
                kong.log.notice("Upstream changed")
            else:
                kong.log.notice("Condition unvalidated")
        
        except Exception as ex:
            kong.log.err("XPath routing failed, exception=", "%s" % (ex))
            # Return a SOAP Fault to the Consumer
            self.ReturnSOAPFault(kong, request, "XPath routing failed", ex)            
        
        kong.log.notice("XPathRouting *** END ***")