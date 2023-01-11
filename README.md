# Kong plugins: XML Handling
It's a set of Kong plugins which are developed in Python and use the Python library [lxml.etree](https://pypi.org/project/lxml/)  binding for the GNOME C libraries [libxml2](https://gitlab.gnome.org/GNOME/libxml2#libxml2) and [libxslt](https://gitlab.gnome.org/GNOME/libxslt#libxslt).

The plugins handle the XML **Request** and the XML **Response** in this order:

**Request**:
1) ```XSLT TRANSFORMATION - BEFORE XSD```: Transform the XML request with XSLT (XSLTransformation) before XSD Validation (step #2)
2) ```XSD VALIDATION```: Validate XML request against its XSD schema
3) ```XSLT TRANSFORMATION - AFTER XSD```: Transform the XML request with XSLT (XSLTransformation) after XSD Validation (step #2)
4) ```ROUTING BY XPATH```: change the Route of the request to a different hostname and path depending of XPath condition

**Response**:
1) ```XSLT TRANSFORMATION - BEFORE XSD```: Transform the XML response before step #2
2) ```XSD VALIDATION```: Validate the XML response against its XSD schema
3) ```XSLT TRANSFORMATION - AFTER XSD```:  Transform the XML response after step #2

Each handling is optional, except the ```XSLT TRANSFORMATION - AFTER XSD``` of the Response.
In case of misconfiguration the Plugin sends to the consumer an HTTP 500 Internal Server Error ```<soap:Fault>``` (with the error detailed message)

## How deploy XML Request Handling plugin
1) Build a new Docker 'Kong Gateway' image with Python dependencies and the plugin code

```
docker build -t kong-gateway-xml-handling .
```

2) Create and prepare a PostgreDB called ```kong-database-xml-handling```.
[See documentation](https://docs.konghq.com/gateway/latest/install/docker/#prepare-the-database).

3) Start the Kong Gateway
```
./start-kong.sh
```

## How configure ```calcWebService/Calc.asmx``` Service in Kong
### Create a Kong Service and route
1) Create a Kong Service named ```calcWebService``` with this URL: https://ecs.syr.edu/faculty/fawcett/Handouts/cse775/code/calcWebService/Calc.asmx.
This simple backend Web Service adds 2 numbers.

2) Create a Route on the Service ```calcWebService``` with the ```path``` value ```/calcWebService```

3) Call the ```calcWebService``` through the Kong Gateway Route by using [httpie](https://httpie.io/) tool
```
http POST http://localhost:8000/calcWebService \
Content-Type:"text/xml; charset=utf-8" \
--raw "<?xml version=\"1.0\" encoding=\"utf-8\"?>
<soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"
xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">
  <soap:Body>
    <Add xmlns=\"http://tempuri.org/\">
      <a>5</a>
      <b>7</b>
    </Add>
  </soap:Body>
</soap:Envelope>"
```

The expected result is ```12```:
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" ...>
  <soap:Body>
    <AddResponse xmlns="http://tempuri.org/">
      <AddResult>12</AddResult>
    </AddResponse>
  </soap:Body>
</soap:Envelope>
```

## How test XML Handling plugins with ```calcWebService/Calc.asmx```
### Example #1: Request | ```XSLT TRANSFORMATION - BEFORE XSD```: adding a Tag in XML request by using XSLT 

The plugin applies a XSLT Transformation on XML request **before** the XSD Validation.
In this example the XSLT **adds the value ```<b>8</b>```** that will be not present in the request.

Add ```xml-request-1-transform-xslt-before``` plugin and configure the plugin with:
- ```XsltTransform``` property with this XSLT definition:
```xml
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output omit-xml-declaration="yes" indent="yes"/>
    <xsl:strip-space elements="*"/>
    <xsl:template match="node()|@*">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>   
    <xsl:template match="//*[local-name()='a']">
       <xsl:copy-of select="."/>
       <b>8</b>
   </xsl:template>
</xsl:stylesheet>
```
Use request defined at step #3, remove ```<b>7</b>```, the expected result is no longer ```12``` but ```13```:
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" ...>
  <soap:Body>
    <AddResponse xmlns="http://tempuri.org/">
      <AddResult>13</AddResult>
    </AddResponse>
  </soap:Body>
</soap:Envelope>
```
### Example #2: Request | ```XSD VALIDATION```: calling incorrectly ```calcWebService``` and detecting issue in the Request with XSD schema
Calling incorrectly ```calcWebService``` and detecting issue in the Request with XSD schema. 
We call incorrectly the Service by injecting a SOAP error; the plugin detects it, sends an error message to the Consumer and Kong doesn't call the SOAP backend API.

Add ```xml-request-2-validate-xsd``` plugin and configure the plugin with:
- ```XsdApiSchema``` property with this value:
```xml
<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" targetNamespace="http://tempuri.org/" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Add" type="tem:AddType" xmlns:tem="http://tempuri.org/"/>
  <xs:complexType name="AddType">
    <xs:sequence>
      <xs:element type="xs:integer" name="a" minOccurs="1"/>
      <xs:element type="xs:integer" name="b" minOccurs="1"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="Subtract" type="tem:SubtractType" xmlns:tem="http://tempuri.org/"/>
  <xs:complexType name="SubtractType">
    <xs:sequence>
      <xs:element type="xs:integer" name="a" minOccurs="1"/>
      <xs:element type="xs:integer" name="b" minOccurs="1"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
```

Use request defined at step #3, **change** ```<soap:Envelope>``` by **```<soap:EnvelopeKong>```** and ```</soap:Envelope>``` by **```</soap:EnvelopeKong>```** => Kong says: 
```xml
<faultstring>XSD validation failed: Element '{http://schemas.xmlsoap.org/soap/envelope/}EnvelopeKong': No matching global declaration available for the validation root. (<string>, line 0)</faultstring>
```
Use request defined at step #3, **remove ```<a>5</a>```** => there is an error because the ```<a>``` tag has the ```minOccurs="1"``` XSD property and Kong says: 
```xml
<faultstring>XSD validation failed: Element '{http://tempuri.org/}b': This element is not expected. Expected is ( {http://tempuri.org/}a ). (<string>, line 0)</faultstring>
```

### Example #3: Request | ```XSLT TRANSFORMATION - AFTER XSD```:  renaming a Tag in XML request by using XSLT
The plugin applies a XSLT Transformation on XML request **after** the XSD Validation.
In this example we **change the Tag name from ```<Subtract>...</Subtract>```** (present in the request) **to ```<Add>...</Add>```**.

Add ```xml-request-3-transform-xslt-after``` plugin and configure the plugin with:
- ```XsltTransform``` property with no value

**Without XSLT**: Use request defined at step #3, rename the Tag ```<Add>...</Add>```, to ```<Subtract>...</Subtract>``` the expected result is ```-3```
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" ...>
  <soap:Body>
    <SubtractResponse xmlns="http://tempuri.org/">
      <SubtractResult>-3</SubtractResult>
    </SubtractResponse>
  </soap:Body>
</soap:Envelope>
```

Configure ```xml-request-3-transform-xslt-after``` plugin with:
- ```XsltTransform``` property with this XSLT definition:
```xml
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output omit-xml-declaration="yes" indent="yes"/>
    <xsl:strip-space elements="*"/>
    <xsl:template match="node()|@*">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>   
    <xsl:template match="//*[local-name()='Subtract']">
       <Add xmlns="http://tempuri.org/"><xsl:apply-templates select="@*|node()" /></Add>
   </xsl:template>
</xsl:stylesheet>
```
**With XSLT**: Use request defined at step #3, rename the Tag ```<Add>...</Add>```, to ```<Subtract>...</Subtract>``` the expected result is ```13```:
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" ...>
  <soap:Body>
    <AddResponse xmlns="http://tempuri.org/">
      <AddResult>13</AddResult>
    </AddResponse>
  </soap:Body>
</soap:Envelope>
```
### Example #4: Request | ```ROUTING BY XPATH```: change the Route of the request to a different hostname and path depending of XPath condition
The plugin searches the XPath entry and compares it to a Condition value. If this is the right Condition value, the plugin changes the host and the path of the Route. 

This example uses a new backend Web Service (https://websrv.cs.fsu.edu/~engelen/calc.wsdl) which provides the same capabilities as ```calcWebService``` Service (https://ecs.syr.edu) defined at step #1. 

Note: the ```websrv.cs.fsu.edu``` introduces a new XML NameSpace so we have to change the XSLT transform to make the proper call.

Add a Kong ```Upstream``` named ```websrv.cs.fsu.edu``` and defines a ```target```with ```websrv.cs.fsu.edu:443``` value. 
Add ```xml-request-4-route-by-xpath``` plugin and configure the plugin with:
- ```RouteToPath``` property with the value ```/~engelen/calcserver.cgi```
- ```RouteToUpstream```property with the value ```websrv.cs.fsu.edu```
- ```XPath``` property with the value ```.//{http://tempuri.org/}a```
- ```XPathCondition``` property with the value ```5```

Open ```xml-request-3-transform-xslt-after``` plugin and configure the plugin with:
- ```XsltTransform``` property with this XSLT definition:
```xml
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output omit-xml-declaration="yes" indent="yes"/>
    <xsl:strip-space elements="*"/>
    <xsl:template match="node()|@*">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
    </xsl:template>
     <xsl:template match="//*[local-name()='Subtract']">
       <urn:add xmlns:urn="urn:calc"><xsl:apply-templates select="@*|node()" /></urn:add>
   </xsl:template>
</xsl:stylesheet>
```
Use request defined at step #3, rename the Tag ```<Add>...</Add>```, to ```<Subtract>...</Subtract>```. The expected result is ```13```. The new Route (to ```websrv.cs.fsu.edu```) sends a slightly different response:
- SOAP tag are in capital letter: ```<SOAP-ENV:Envelope>``` instead of ```<soap:Envelope>```
- Namespace is injected: ```xmlns:ns="urn:calc"```
```xml

<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" ... xmlns:ns="urn:calc">
  <SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <ns:addResponse>
      <result>13</result>
    </ns:addResponse>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```
### Example #5: Response | ```XSLT TRANSFORMATION - BEFORE XSD```: changing a Tag name in XML response by using XSLT
The plugin applies a XSLT Transformation on XML response **before** the XSD Validation.
In this example the XSLT **changes the Tag name from ```<result>...</result>```** (present in the response) **to ```<KongResult>...</KongResult>```**.

- Add ```xml-response-3-transform-xslt-after```   plugin with default parameters
- Add ```xml-response-2-validate-xsd```           plugin with default parameters
- Add ```xml-response-1-transform-xslt-before```  plugin and configure the plugin with:
  - ```XsltTransform``` property with this XSLT definition:
```xml
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
    </xsl:template>
    <xsl:template match="//*[local-name()='addResponse']">
      <addResponse>
        <xsl:apply-templates select="@*|node()" />
      </addResponse>
  </xsl:template>
  <xsl:template match="//*[local-name()='result']">
    <KongResult><xsl:apply-templates select="@*|node()" /></KongResult>
  </xsl:template>
</xsl:stylesheet>
```
Use request defined at step #3, rename the Tag ```<Add>...</Add>```, to ```<Subtract>...</Subtract>``` the expected result is ```<KongResult>13</KongResult>```:
```xml
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" ... xmlns:ns="urn:calc">
  <SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <ns:addResponse>
      <KongResult>13</KongResult>
    </ns:addResponse>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
```
### Example #6: Response | ```XSD VALIDATION```: checking validity of XML response against its XSD schema
Configure ```xml-response-2-validate-xsd``` plugin with:
- ```XsdApiSchema``` property with this value:
```xml
<xs:schema attributeFormDefault="unqualified" elementFormDefault="qualified" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="addResponse" type="addResponseType"/>
  <xs:complexType name="addResponseType">
    <xs:sequence>
      <xs:element type="xs:string" name="KongResult"/>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
```
