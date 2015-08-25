<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Sync Repository Import

         CSV fields:
         UUID............................sync_repository.uuid
         Name............................sync_repository.name
         Type............................sync_repository.apitype
                                         - eden, ccrm, wrike, mcb, adashi
         Accept Push.....................sync_repository.accept_push
                                         - true or false

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

        <resource name="sync_repository">
            <xsl:attribute name="uuid">
                <xsl:value-of select="col[@field='UUID']"/>
            </xsl:attribute>
            
            <data field="name">
                <xsl:value-of select="col[@field='Name']"/>
            </data>
            
            <data field="apitype">
                <xsl:value-of select="col[@field='Type']"/>
            </data>
            
            <xsl:variable name="AcceptPush" select="col[@field='Accept Push']/text()"/>
            
            <data field="accept_push">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$AcceptPush='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
