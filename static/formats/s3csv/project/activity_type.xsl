<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Activity Types - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Name
         Comments.............string..........Comments
         Sector:<Sector Abrv>.Yes/blank.......Flag to link activity type to Sector 

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
            <!-- Sectors -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Sector')]">
                <xsl:call-template name="Sector"/>
            </xsl:for-each>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="project_activity_type">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            <xsl:variable name="RowNumber" select="position()"/>
            
            <!-- Loop through sector columns-->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Sector')]">
                <xsl:variable name="ColumnName" select="@field"/>
                
                <!-- Test if this sector has been marked for this them -->
                <xsl:if test="//row[$RowNumber]/col[@field=$ColumnName] != ''">
                    <resource name="project_activity_type_sector">
                        <reference field="sector_id" resource="org_sector">
                            <xsl:attribute name="tuid">
                                <xsl:value-of  select="normalize-space(substring-after(@field, ':'))"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
            </xsl:for-each>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->
    <xsl:template name="Sector">
        <xsl:variable name="Sector" select="normalize-space(substring-after(@field, ':'))"/>

        <resource name="org_sector">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Sector"/>
            </xsl:attribute>
            <data field="abrv"><xsl:value-of select="$Sector"/></data>
        </resource>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>