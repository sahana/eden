<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Contacts - CSV Import Stylesheet
         
         2012-Jan-05 / Fran Boon <fran AT aidiq DOT com>

         CSV fields:
         First Name..............pr_person
         Middle Name.............pr_person
         Last Name...............pr_person
         Initials................pr_person
         Email...................pr_contact

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the Contact -->
        <resource name="pr_contact">
            <!-- Create the Person -->
            <reference field="pe_id" resource="pr_person">
                <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
                <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
                <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            </reference>
            <data field="contact_method"><xsl:text>SMS</xsl:text></data>
            <data field="value"><xsl:value-of select="col[@field='Email']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
