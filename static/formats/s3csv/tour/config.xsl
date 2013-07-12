<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Tour Config - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be tour/config/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Name............................tour_config.name
         Code............................tour_config.code
         Controller......................tour_config.controller
         Function........................tour_config.function
         Autostart.......................tour_config.autostart
         Authenticated...................tour_config.authenticated

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Tour Config -->
        <resource name="tour_config">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="controller"><xsl:value-of select="col[@field='Controller']"/></data>
            <data field="function"><xsl:value-of select="col[@field='Function']"/></data>
            <xsl:if test="col[@field='Autostart']='T'">
                <data field="autostart" value="true">True</data>
            </xsl:if>
            <xsl:if test="col[@field='Authenticated']='T'">
                <data field="authenticated" value="true">True</data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
