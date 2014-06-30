<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Services - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Service.................org_service.name or org_service.parent
         SubService..............org_service.name or org_service.parent
         SubSubService...........org_service.name or org_service.parent
         Comments................org_service.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:variable name="ServicePrefix" select="'Service:'"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="service" match="row" use="concat(col[@field='Service'], '/',
                                                    col[@field='SubService'], '/',
                                                    col[@field='SubSubService'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Services -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('service',
                                                                   concat(col[@field='Service'], '/',
                                                                          col[@field='SubService'], '/',
                                                                          col[@field='SubSubService']))[1])]">
                <xsl:call-template name="OrganisationService">
                    <xsl:with-param name="Service">
                         <xsl:value-of select="col[@field='Service']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubService">
                         <xsl:value-of select="col[@field='SubService']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubSubService">
                         <xsl:value-of select="col[@field='SubSubService']"/>
                    </xsl:with-param>
                    <xsl:with-param name="Comments">
                         <xsl:value-of select="col[@field='Comments']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Done
            <xsl:apply-templates select="table/row"/> -->
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrganisationService">
        <xsl:param name="Service"/>
        <xsl:param name="SubService"/>
        <xsl:param name="SubSubService"/>
        <xsl:param name="Comments"/>

        <!-- @todo: migrate to Taxonomy-pattern, see vulnerability/data.xsl -->
        <resource name="org_service">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($ServicePrefix, $Service)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Service"/></data>
            <xsl:if test="$Comments!='' and $SubService=''">
                <data field="comments"><xsl:value-of select="$Comments"/></data>
            </xsl:if>
        </resource>
        <xsl:if test="$SubService!=''">
            <resource name="org_service">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ServicePrefix, $Service, '/', $SubService)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$SubService"/></data>
                <xsl:if test="$Comments!='' and $SubSubService=''">
                    <data field="comments"><xsl:value-of select="$Comments"/></data>
                </xsl:if>
                <reference field="parent" resource="org_service">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($ServicePrefix, $Service)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>
        <xsl:if test="$SubSubService!=''">
            <resource name="org_service">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ServicePrefix, $Service, '/', $SubService, '/', $SubSubService)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$SubSubService"/></data>
                <xsl:if test="$Comments!=''">
                    <data field="comments"><xsl:value-of select="$Comments"/></data>
                </xsl:if>
                <reference field="parent" resource="org_service">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($ServicePrefix, $Service, '/', $SubService)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

</xsl:stylesheet>
