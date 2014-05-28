<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Persons - CSV Import Stylesheet

         CSV column...........Format..........Content

         First Name.................required..........person first name
         Last Name..................required..........person last name
         Person Gender..............optional..........person gender
         DOB........................optional..........person date of birth
         Place of Birth.............optional..........person_details place of birth
         Fiscal Code................optional..........evr_case fiscal code

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        
        <xsl:variable name="gender">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$PersonGender"/>
            </xsl:call-template>
        </xsl:variable>
        
        <resource name="pr_person">
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="date_of_birth"><xsl:value-of select="col[@field='Date of Birth']"/></data>
            <resource name="pr_person_details">
                <xsl:if test="col[@field='Place of Birth']!=''">
                    <data field="place_of_birth"><xsl:value-of select="col[@field='Place of Birth']"/></data>
                </xsl:if>
            </resource>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>
            <resource name="evr_case">
                <xsl:if test="col[@field='Fiscal Code']!=''">
                    <data field="fiscal_code"><xsl:value-of select="col[@field='Fiscal Code']"/></data>
                </xsl:if>
            </resource>
        </resource>
        
    </xsl:template>

</xsl:stylesheet>