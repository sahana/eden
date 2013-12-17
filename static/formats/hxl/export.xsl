<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hxl="http://hxl.humanitarianresponse.info/ns/#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<!--xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:foaf="http://xmlns.com/foaf/0.1/"
    xmlns:geo="http://www.opengis.net/ont/geosparql#"-->

    <!-- **********************************************************************
         HXL Export Templates for Sahana Eden

         Copyright (c) 2013 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Used by base.xsl -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>
    <xsl:param name="title"/>
    <xsl:param name="prefix"/>
    <xsl:param name="name"/>
    <xsl:param name="id"/>
    <xsl:param name="alias"/>
    <xsl:param name="component"/>
    <xsl:param name="mode"/>
    <xsl:param name="utcnow"/>

    <!-- ****************************************************************** -->
    <!-- Defaults if no special case provided here -->
    <xsl:include href="base.xsl"/>
    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- HXL URIs -->
    <xsl:variable name="ActivityPrefix">
        <xsl:text>http://hxl.humanitarianresponse.info/data/emergencies/</xsl:text>
    </xsl:variable>
        
    <xsl:variable name="EventPrefix">
        <xsl:text>http://hxl.humanitarianresponse.info/data/emergencies/</xsl:text>
    </xsl:variable>
        
    <xsl:variable name="LocationPrefix">
        <xsl:text>http://hxl.humanitarianresponse.info/data/locations/admin/</xsl:text>
    </xsl:variable>
        
    <xsl:variable name="OrgPrefix">
        <xsl:text>http://hxl.humanitarianresponse.info/data/organisations/</xsl:text>
    </xsl:variable>
        
    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='event_event']">
        <!-- Sahana resource -->
        <xsl:variable name="sahana_url">
            <xsl:call-template name="event_url">
                <xsl:with-param name="uuid" select="./@uuid" />
            </xsl:call-template>
        </xsl:variable>
        <rdf:Description>
            <xsl:attribute name="rdf:about">
                <xsl:value-of select="$sahana_url"/>
            </xsl:attribute>
            <hxl:Emergency>
                <xsl:value-of select="./data[@field='name']"/>
            </hxl:Emergency>
        </rdf:Description>
        <!-- Link to GLIDE -->
        <xsl:variable name="glide">
            <xsl:value-of select="./resource[@name='event_event_tag' and data[@field='tag']='GLIDE']/data[@field='value']/text()" />
        </xsl:variable>
        <xsl:if test="$glide!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:hasGLIDEnumber>
                    <xsl:value-of select="$glide"/>
                </hxl:hasGLIDEnumber>
                <!-- @ToDo: Link to GLIDE resource -->
            </rdf:Description>
        </xsl:if>
        <!-- Link to OCHA FTS -->
        <xsl:variable name="fts_code">
            <xsl:value-of select="./resource[@name='event_event_tag' and data[@field='tag']='OCHA_FTS']/data[@field='value']/text()" />
        </xsl:variable>
        <xsl:if test="$fts_code!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <seeAlso>
                    <xsl:attribute name="rdf:resource">
                        <xsl:value-of select="concat($EventPrefix, $fts_code)"/>
                    </xsl:attribute>
                </seeAlso>
            </rdf:Description>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_location']">
        <!-- Sahana resource -->
        <xsl:variable name="sahana_url">
            <xsl:call-template name="location_url">
                <xsl:with-param name="uuid" select="./@uuid" />
            </xsl:call-template>
        </xsl:variable>
        <rdf:Description>
            <xsl:attribute name="rdf:about">
                <xsl:value-of select="$sahana_url"/>
            </xsl:attribute>
            <hxl:featureName>
                <xsl:value-of select="./data[@field='name']"/>
            </hxl:featureName>
        </rdf:Description>
        <xsl:variable name="level">
            <xsl:value-of select="./data[@field='level']"/>
        </xsl:variable>
        <xsl:if test="$level!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:atLevel>
                    <xsl:value-of select="substring($level, 2, 2)"/>
                </hxl:atLevel>
            </rdf:Description>
        </xsl:if>
        <xsl:variable name="parent">
            <xsl:value-of select="./reference[@field='parent']/@uuid"/>
        </xsl:variable>
        <xsl:if test="$parent!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:atLocation>
                    <xsl:attribute name="rdf:resource">
                        <xsl:call-template name="location_url">
                            <xsl:with-param name="uuid" select="$parent" />
                        </xsl:call-template>
                    </xsl:attribute>
                </hxl:atLocation>
            </rdf:Description>
        </xsl:if>
        <xsl:variable name="pcode">
            <xsl:value-of select="./resource[@name='gis_location_tag' and data[@field='tag']='PCode']/data[@field='value']/text()" />
        </xsl:variable>
        <xsl:if test="$pcode!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:pcode>
                    <xsl:value-of select="$pcode"/>
                </hxl:pcode>
            </rdf:Description>
        </xsl:if>
        <xsl:if test="$pcode!=''">
            <xsl:variable name="L0">
                <xsl:value-of select="/data[@field='L0']/@value" />
            </xsl:variable>
            <xsl:variable name="ISO3">
                <xsl:value-of select="//resource[@name='gis_location' and data[@field='level']='L0' and data[@field='name']=$L0]/resource[@name='gis_location_tag' and data[@field='tag']='ISO3']/data[@field='value']" />
            </xsl:variable>
            <xsl:if test="$ISO3!=''">
                <!-- Link to HXL resource -->
                <rdf:Description>
                    <xsl:attribute name="rdf:about">
                        <xsl:value-of select="$sahana_url"/>
                    </xsl:attribute>
                    <seeAlso>
                        <xsl:attribute name="rdf:resource">
                            <xsl:value-of select="concat($LocationPrefix, $ISO3, '/', $code)"/>
                        </xsl:attribute>
                    </seeAlso>
                </rdf:Description>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='org_organisation']">
        <!-- Sahana resource -->
        <xsl:variable name="sahana_url">
            <xsl:call-template name="organisation_url">
                <xsl:with-param name="uuid" select="./@uuid" />
            </xsl:call-template>
        </xsl:variable>
        <rdf:Description>
            <xsl:attribute name="rdf:about">
                <xsl:value-of select="$sahana_url"/>
            </xsl:attribute>
            <hxl:orgName>
                <xsl:value-of select="./data[@field='name']"/>
            </hxl:orgName>
        </rdf:Description>
        <xsl:variable name="acronym">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string" select="./data[@field='acronym']/text()" />
            </xsl:call-template>
        </xsl:variable>
        <xsl:if test="$acronym!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:abbreviation>
                    <xsl:value-of select="./data[@field='acronym']"/>
                </hxl:abbreviation>
            </rdf:Description>
        </xsl:if>
        <!-- Website -->
        <xsl:variable name="website">
            <xsl:value-of select="./data[@field='website']"/>
        </xsl:variable>
        <xsl:if test="$website!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:organisationHomepage>
                    <xsl:value-of select="$website"/>
                </hxl:organisationHomepage>
            </rdf:Description>
        </xsl:if>
        <!-- Link to OCHA FTS
             @ToDo: org_organisation_tag table -->
        <xsl:variable name="ftsId">
            <xsl:value-of select="./resource[@name='org_organisation_tag' and data[@field='tag']='OCHA_FTS']/data[@field='value']/text()" />
        </xsl:variable>
        <xsl:if test="$ftsId!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:ftsId>
                    <xsl:value-of select="$ftsId"/>
                </hxl:ftsId>
            </rdf:Description>
        </xsl:if>
        <xsl:if test="$acronym!=''">
            <!-- Link to HXL resource -->
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <seeAlso>
                    <xsl:attribute name="rdf:resource">
                        <xsl:value-of select="concat($OrgPrefix, $acronym)"/>
                    </xsl:attribute>
                </seeAlso>
            </rdf:Description>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='project_activity']">
        <!-- Sahana resource -->
        <xsl:variable name="sahana_url">
            <xsl:call-template name="activity_url">
                <xsl:with-param name="uuid" select="./@uuid" />
            </xsl:call-template>
        </xsl:variable>
        <!-- Activity -->
        <xsl:variable name="activity">
            <xsl:value-of select="./data[@field='name']" />
        </xsl:variable>
        <xsl:if test="$activity!=''">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:Response>
                    <xsl:value-of select="$activity" />
                </hxl:Response>
            </rdf:Description>
            <!-- Beneficiaries -->
            <xsl:for-each select="./resource[@name='project_beneficiary_activity']">
                <xsl:variable name="beneficiary_id">
                    <xsl:value-of select="./reference[@field='beneficiary_id']/@uuid" />
                </xsl:variable>
                <rdf:Description>
                    <xsl:attribute name="rdf:about">
                        <xsl:value-of select="$sahana_url"/>
                    </xsl:attribute>
                    <hxl:personCount>
                        <xsl:value-of select="//resource[@uuid=$beneficiary_id]/data[@field='value']/@value" />
                    </hxl:personCount>
                </rdf:Description>
            </xsl:for-each>
            <!-- Date -->
            <xsl:variable name="date">
                <xsl:value-of select="./data[@field='date']" />
            </xsl:variable>
            <xsl:if test="$date!=''">
                <rdf:Description>
                    <xsl:attribute name="rdf:about">
                        <xsl:value-of select="$sahana_url"/>
                    </xsl:attribute>
                    <hxl:date>
                        <xsl:value-of select="$date" />
                    </hxl:date>
                </rdf:Description>
            </xsl:if>
            <!-- Location -->
            <xsl:variable name="location_id">
                <xsl:value-of select="./reference[@field='location_id']/@uuid" />
            </xsl:variable>
            <xsl:if test="$location_id!=''">
                <rdf:Description>
                    <xsl:attribute name="rdf:about">
                        <xsl:value-of select="$sahana_url"/>
                    </xsl:attribute>
                    <hxl:atLocation>
                        <xsl:attribute name="rdf:resource">
                            <xsl:call-template name="location_url">
                                <xsl:with-param name="uuid" select="$location_id" />
                            </xsl:call-template>
                        </xsl:attribute>
                    </hxl:atLocation>
                </rdf:Description>
            </xsl:if>
        </xsl:if>
        <!-- Organisations -->
        <xsl:for-each select="./resource[@name='project_activity_organisation']">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:Organisation>
                    <xsl:attribute name="rdf:resource">
                        <xsl:call-template name="organisation_url">
                            <xsl:with-param name="uuid" select="./reference[@field='organisation_id']/@uuid" />
                        </xsl:call-template>
                    </xsl:attribute>
                </hxl:Organisation>
            </rdf:Description>
        </xsl:for-each>
        <!-- Distributions -->
        <xsl:for-each select="./resource[@name='supply_distribution']">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:Distribution>
                    <xsl:value-of select="./reference[@field='parameter_id']/text()" />
                </hxl:Distribution>
            </rdf:Description>
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:count>
                    <xsl:value-of select="./data[@field='value']/@value" />
                </hxl:count>
            </rdf:Description>
            <!-- Date -->
            <xsl:variable name="date">
                <xsl:value-of select="./data[@field='date']" />
            </xsl:variable>
            <xsl:if test="$date!=''">
                <rdf:Description>
                    <xsl:attribute name="rdf:about">
                        <xsl:value-of select="$sahana_url"/>
                    </xsl:attribute>
                    <hxl:date>
                        <xsl:value-of select="$date" />
                    </hxl:date>
                </rdf:Description>
            </xsl:if>
            <!-- Location -->
            <xsl:variable name="location_id">
                <xsl:value-of select="./reference[@field='location_id']/@uuid" />
            </xsl:variable>
            <xsl:if test="$location_id!=''">
                <rdf:Description>
                    <xsl:attribute name="rdf:about">
                        <xsl:value-of select="$sahana_url"/>
                    </xsl:attribute>
                    <hxl:atLocation>
                        <xsl:attribute name="rdf:resource">
                            <xsl:call-template name="location_url">
                                <xsl:with-param name="uuid" select="$location_id" />
                            </xsl:call-template>
                        </xsl:attribute>
                    </hxl:atLocation>
                </rdf:Description>
            </xsl:if>
        </xsl:for-each>
        <!-- Events -->
        <xsl:for-each select="./resource[@name='event_activity']">
            <rdf:Description>
                <xsl:attribute name="rdf:about">
                    <xsl:value-of select="$sahana_url"/>
                </xsl:attribute>
                <hxl:aboutEmergency>
                    <xsl:attribute name="rdf:resource">
                        <xsl:call-template name="event_url">
                            <xsl:with-param name="uuid" select="./reference[@field='event_id']/@uuid" />
                        </xsl:call-template>
                    </xsl:attribute>
                </hxl:aboutEmergency>
            </rdf:Description>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
