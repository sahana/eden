<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Sync Dataset Import

         CSV fields:

         Repository......................sync_repository.name
         Code............................sync_dataset.code

    *********************************************************************** -->
    <xsl:import href="common.xsl"/>

    <xsl:output method="xml"/>

    <!-- Index for repositories -->
    <xsl:key name="repositories" match="row" use="col[@field='Repository']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Create repositories -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('repositories',
                                                                       col[@field='Repository'])[1])]">
                <xsl:call-template name="Repository"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Repository" select="col[@field='Repository']/text()"/>
        <xsl:variable name="Code" select="col[@field='Code']/text()"/>

        <xsl:if test="$Repository!='' and $Code!=''">
            <resource name="sync_dataset">
                <reference field="repository_id" resource="sync_repository">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('REPOSITORY:', $Repository)"/>
                    </xsl:attribute>
                </reference>
                <data field="code">
                    <xsl:value-of select="$Code"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>
