<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml"/>

    <xsl:key name="disease" match="row" use="col[@field='Disease']"/>
    
    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('disease', col[@field='Disease'])[1])]">
                <xsl:call-template name="Disease"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Disease">
        <xsl:variable name="Disease" select="col[@field='Disease']/text()"/>
        <resource name="disease_disease">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Disease:', $Disease)"/>
            </xsl:attribute>
            <data field="name">
                <xsl:value-of select="$Disease"/>
            </data>
        </resource>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Disease" select="col[@field='Disease']/text()"/>
        <resource name="disease_symptom">

            <reference field="disease_id" resource="disease_disease">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Disease:', $Disease)"/>
                </xsl:attribute>
            </reference>
        
            <data field="name">
                <xsl:value-of select="col[@field='Name']/text()"/>
            </data>

            <xsl:variable name="Description" select="col[@field='Description']/text()"/>
            <xsl:if test="$Description!=''">
                <data field="description">
                    <xsl:value-of select="$Description"/>
                </data>
            </xsl:if>
                
            <xsl:variable name="Assessment" select="col[@field='Assessment']/text()"/>
            <xsl:if test="$Assessment!=''">
                <data field="assessment">
                    <xsl:value-of select="$Assessment"/>
                </data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
