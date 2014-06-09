<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation Group Membership Status - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Status Name
         Description..........string..........Status Comments

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
        <resource name="org_group_membership_status">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Description']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
