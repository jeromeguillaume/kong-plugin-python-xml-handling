xml-request-1-transform-xslt-before   PRIORITY = 50
xml-request-2-validate-xsd            PRIORITY = 45
xml-request-3-transform-xslt-after    PRIORITY = 40
xml-request-4-route-by-xpath          PRIORITY = 35
xml-response-1-transform-xslt-before  PRIORITY = 30
xml-response-2-validate-xsd           PRIORITY = 25
xml-response-3-transform-xslt-after   PRIORITY = 20

# 1) Create a service on: https://www.dataaccess.com:443/webservicesserver/NumberConversion.wso
# 2) Create a Route on service created above: path=/NumberConversion
# 3) Call the Route with:
http POST :8000/NumberConversion Content-Type:"application/soap+xml" \
    --raw "<?xml version='1.0' encoding=\"utf-8\"?>\
    <soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
      <soap:Body>\
       <NumberToWords xmlns=\"http://www.dataaccess.com/webservicesserver/\">\
          <ubiNum>300</ubiNum>\
        </NumberToWords>\
      </soap:Body>\
    </soap:Envelope>"

# https://www.w3schools.com/xml/tempconvert.asmx?WSDL
# https://www.w3schools.com/xml/tempconvert.asmx
http POST :8000/tempconvert op==CelsiusToFahrenheit Content-Type:"text/xml" \
  SOAPAction: "https://www.w3schools.com/xml/CelsiusToFahrenheit" \
    --raw "<?xml version=\"1.0\" encoding=\"utf-8\"?>\
<soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
  <soap:Body>\
    <CelsiusToFahrenheit xmlns=\"https://www.w3schools.com/xml/\">\
      <Celsius>55</Celsius>\
    </CelsiusToFahrenheit>\
  </soap:Body>\
</soap:Envelope>"

#http POST https://ecs.syr.edu/faculty/fawcett/Handouts/cse775/code/calcWebService/Calc.asmx \
http POST http://localhost:8000/calcWebService \
Content-Type:"text/xml; charset=utf-8" \
SOAPAction: "http://tempuri.org/Add" \
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