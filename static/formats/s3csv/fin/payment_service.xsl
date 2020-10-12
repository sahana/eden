<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Payment Service - CSV Import Stylesheet
         
         CSV column...........Format..........Content

         Name.................string..........Name
         URL..................string..........Base URL
         Username.............string..........Username (Client ID)
         Password.............string..........Password (Client Secret)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="fin_payment_size">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="base_url"><xsl:value-of select="col[@field='URL']"/></data>
            <data field="username"><xsl:value-of select="col[@field='Username']"/></data>
            <data field="password"><xsl:value-of select="col[@field='Password']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
