<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         AUTH Processing Types - CSV Import Stylesheet

         CSV column..................Format..........Content

         Code........................string..........Unique Type Code
         Name........................string..........Type Name
         Comments....................string..........Comments

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

        <xsl:variable name="Code" select="normalize-space(col[@field='Code']/text())"/>
        <xsl:variable name="Name" select="normalize-space(col[@field='Name']/text())"/>

        <resource name="auth_processing_type">
            <data field="code">
                <xsl:value-of select="$Code"/>
            </data>
            <data field="name">
                <xsl:value-of select="$Name"/>
            </data>
            <data field="comments">
                <xsl:value-of select="col[@field='Comments']/text()"/>
            </data>
        </resource>

    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>
