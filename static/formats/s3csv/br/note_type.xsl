<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         BR Note Type - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Type Name
         Code.................string..........Unique Type Code (required)
         Comments.............string..........Comments

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
        <resource name="br_note_type">
            <data field="name"><xsl:value-of select="col[@field='Name']/text()"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']/text()"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']/text()"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
