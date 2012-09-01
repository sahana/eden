<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Doc Source Type - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Instance type..................required.....doc_source_type.doc_source_instance
         Name...........................required.....doc_source_type.name
         Display........................required.....doc_source_type.display

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">

        <s3xml>
            <!-- Create the Doc Source Type records -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!--  Doc Source Type Record -->
    <xsl:template match="row">

        <resource name="doc_source_type">
            <data field="doc_source_instance"><xsl:value-of select="col[@field='Instance type']"/></data>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="display"><xsl:value-of select="col[@field='Display']"/></data>
        </resource>

    </xsl:template>

</xsl:stylesheet>
