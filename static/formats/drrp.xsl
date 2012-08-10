<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Projects - Stylesheet to migrate from DRRPP v1 to v2
    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:include href="xml/commons.xsl"/>
    <xsl:include href="xml/countries.xsl"/>

    <xsl:variable name="HazardPrefix" select="'Hazard:'"/>
    <xsl:variable name="ThemePrefix" select="'Theme:'"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./s3xrc"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="s3xrc">
        <xsl:for-each select="//resource[@name='drrpp_file']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_framework_file']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_framework']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_group']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_organisation']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_output']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_project']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_link']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='org_organisation']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='pr_person']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='auth_user']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <resource name="org_organisation_type">
            <xsl:attribute name="tuid">OrgType:Committees/Mechanism/Forum</xsl:attribute>
            <data field="name">Committees/Mechanism/Forum</data>
        </resource>
        <resource name="org_organisation_type">
            <xsl:attribute name="tuid">OrgType:Network</xsl:attribute>
            <data field="name">Network</data>
        </resource>
        <resource name="org_organisation_type">
            <xsl:attribute name="tuid">OrgType:Regional Organisation</xsl:attribute>
            <data field="name">Regional Organisation</data>
        </resource>
        <resource name="org_organisation_type">
            <xsl:attribute name="tuid">OrgType:Regional Office</xsl:attribute>
            <data field="name">Regional Office</data>
        </resource>
        <resource name="org_organisation_type">
            <xsl:attribute name="tuid">OrgType:Regional Center</xsl:attribute>
            <data field="name">Regional Center</data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_project']">

        <xsl:variable name="Status" select="data[@field='status_id']"/>
        <xsl:variable name="Countries" select="data[@field='country_dummy']"/>
        <xsl:variable name="LeadOrganisation" select="reference[@field='lead_organisation_id']/@uuid"/>
        <xsl:variable name="ContactOrganisation" select="reference[@field='contact_organisation_id']/@uuid"/>
        <xsl:variable name="ContactName" select="data[@field='contact_name']"/>
        <xsl:variable name="ContactEmail" select="data[@field='contact_email']"/>
        <xsl:variable name="ContactPhone" select="data[@field='contact_phone']"/>
        <xsl:variable name="HFA" select="data[@field='hfa_ids']/@value"/>
        <xsl:variable name="RFA" select="data[@field='rfa_ids']/@value"/>
        <xsl:variable name="Hazards" select="data[@field='hazard_ids']"/>
        <xsl:variable name="Themes" select="data[@field='theme_ids']"/>

        <resource name="project_project">

            <xsl:attribute name="tuid">
                <xsl:value-of select="@uuid"/>
            </xsl:attribute>
            <xsl:attribute name="created_on">
                <xsl:value-of select="@created_on"/>
            </xsl:attribute>
            <xsl:attribute name="modified_on">
                <xsl:value-of select="@modified_on"/>
            </xsl:attribute>
            <xsl:attribute name="created_by">
                <xsl:value-of select="@created_by"/>
            </xsl:attribute>
            <xsl:attribute name="modified_by">
                <xsl:value-of select="@modified_by"/>
            </xsl:attribute>

            <xsl:if test="data[@field='approved']='True'">
                <xsl:attribute name="approved_by">
                    <xsl:value-of select="@modified_by"/>
                </xsl:attribute>
            </xsl:if>

            <data field="name"><xsl:value-of select="data[@field='name']"/></data>
            <data field="code"><xsl:value-of select="data[@field='short_title']"/></data>
            <data field="description"><xsl:value-of select="data[@field='description']"/></data>
            <data field="start_date"><xsl:value-of select="data[@field='start_date']/@value"/></data>
            <data field="end_date"><xsl:value-of select="data[@field='end_date']/@value"/></data>
            <data field="budget"><xsl:value-of select="data[@field='total_funding']/@value"/></data>
            <data field="currency">USD</data>
            <data field="objectives"><xsl:value-of select="data[@field='objectives']"/></data>
            <data field="comments"><xsl:value-of select="data[@field='comments']"/></data>

            <xsl:if test="$Status">
                <reference field="status_id" resource="project_status">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Status"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <data field="hfa">
                [<xsl:value-of select="translate(substring($HFA, 2, string-length($HFA) - 2), '|', ',')"/>]
            </data>

            <resource name="project_drrpp">
                <xsl:if test="data[@field='parent_project']!='None'">
                    <data field="parent_project"><xsl:value-of select="data[@field='parent_project']"/></data>
                </xsl:if>
                <data field="duration"><xsl:value-of select="data[@field='duration']"/></data>
                <data field="outputs"><xsl:value-of select="data[@field='outputs']"/></data>
                <data field="rfa">
                    [<xsl:value-of select="translate(substring($RFA, 2, string-length($RFA) - 2), '|', ',')"/>]
                </data>
            </resource>

            <xsl:if test="$ContactOrganisation!='' and $ContactName!=''">
                <reference field="human_resource_id" resource="hrm_human_resource">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('HR:',$ContactOrganisation,$ContactName)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:if test="$LeadOrganisation!=''">
                <resource name="project_organisation">
                    <!-- Lead Implementer -->
                    <data field="role">1</data>
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$LeadOrganisation"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='impl_org_dummy']"/></xsl:with-param>
                <xsl:with-param name="arg">impl_org</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='funding_dummy']"/></xsl:with-param>
                <xsl:with-param name="arg">donor</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='file_dummy']"/></xsl:with-param>
                <xsl:with-param name="arg">file</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='link_dummy']"/></xsl:with-param>
                <xsl:with-param name="arg">link</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='output_dummy']"/></xsl:with-param>
                <xsl:with-param name="listsep">;</xsl:with-param>
                <xsl:with-param name="arg">output</xsl:with-param>
            </xsl:call-template>

            <!-- Project Hazards -->
            <xsl:if test="$Hazards!=''">
                <reference field="multi_hazard_id" resource="project_hazard">
                    <xsl:attribute name="tuid">
                        <xsl:variable name="HazardList">
                            <xsl:call-template name="quoteList">
                                <xsl:with-param name="prefix"><xsl:value-of select="'Hazard:'"/></xsl:with-param>
                                <xsl:with-param name="list"><xsl:value-of select="$Hazards"/></xsl:with-param>
                            </xsl:call-template>
                        </xsl:variable>
                        <xsl:value-of select="concat('[', $HazardList, ']')"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Project Themes -->
            <xsl:if test="$Themes!=''">
                <!-- Embedded within record -->
                <reference field="multi_theme_id" resource="project_theme">
                    <xsl:attribute name="tuid">
                        <xsl:variable name="ThemeList">
                            <xsl:call-template name="quoteList">
                                <xsl:with-param name="prefix"><xsl:value-of select="'Theme:'"/></xsl:with-param>
                                <xsl:with-param name="list"><xsl:value-of select="$Themes"/></xsl:with-param>
                            </xsl:call-template>
                        </xsl:variable>
                        <xsl:value-of select="concat('[', $ThemeList, ']')"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Countries -->
            <xsl:choose>
                <xsl:when test="$Countries=''">
                </xsl:when>
                <xsl:when test="$Countries='Pacific'">
                    <data field="region"><xsl:value-of select="$Countries"/></data>
                </xsl:when>
                <xsl:when test="$Countries='South Asia'">
                    <data field="region"><xsl:value-of select="$Countries"/></data>
                </xsl:when>
                <xsl:when test="$Countries='South East Asia'">
                    <data field="region"><xsl:value-of select="$Countries"/></data>
                </xsl:when>
                <xsl:when test="$Countries='East, Central and West Asia'">
                    <data field="region"><xsl:value-of select="$Countries"/></data>
                </xsl:when>
                <xsl:otherwise>
                    <reference field="countries_id" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:variable name="CountryCodes">
                                <xsl:call-template name="splitList">
                                    <xsl:with-param name="arg">countrycode</xsl:with-param>
                                    <!--<xsl:with-param name="listsep">;</xsl:with-param>-->
                                    <xsl:with-param name="list">
                                        <xsl:value-of select="$Countries"/>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:variable>
                            <xsl:if test="starts-with($CountryCodes, ',&quot;')">
                                <xsl:value-of select="concat('[', substring-after($CountryCodes, ','), ']')"/>
                            </xsl:if>
                        </xsl:attribute>
                    </reference>
                </xsl:otherwise>
            </xsl:choose>

        </resource>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Hazards"/></xsl:with-param>
            <xsl:with-param name="arg">hazard</xsl:with-param>
        </xsl:call-template>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Themes"/></xsl:with-param>
            <xsl:with-param name="arg">theme</xsl:with-param>
        </xsl:call-template>

        <xsl:if test="$Status">
            <resource name="project_status">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Status"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Status"/></data>
            </resource>
        </xsl:if>

        <xsl:if test="$ContactOrganisation!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ContactOrganisation"/>
                </xsl:attribute>

                <data field="name"><xsl:value-of select="reference[@field='contact_organisation_id']"/></data>

                <xsl:if test="$ContactName!=''">
                    <resource name="hrm_human_resource">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('HR:',$ContactOrganisation,$ContactName)"/>
                        </xsl:attribute>
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('PR:',$ContactOrganisation,$ContactName)"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
            </resource>
            <xsl:if test="$ContactName!=''">
                <resource name="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('PR:',$ContactOrganisation,$ContactName)"/>
                    </xsl:attribute>
                    <xsl:choose>
                        <xsl:when test="contains($ContactName, ' ')">
                            <xsl:variable name="first" select="substring-before($ContactName, ' ')"/>
                            <xsl:choose>
                                <xsl:when test="$first='Mr.'">
                                    <data field="gender">3</data>
                                    <xsl:variable name="second" select="substring-after($ContactName, ' ')"/>
                                    <data field="first_name"><xsl:value-of select="substring-before($second, ' ')"/></data>
                                    <data field="last_name"><xsl:value-of select="substring-after($second, ' ')"/></data>
                                </xsl:when>
                                <xsl:when test="$first='Ms.'">
                                    <data field="gender">2</data>
                                    <xsl:variable name="second" select="substring-after($ContactName, ' ')"/>
                                    <data field="first_name"><xsl:value-of select="substring-before($second, ' ')"/></data>
                                    <data field="last_name"><xsl:value-of select="substring-after($second, ' ')"/></data>
                                </xsl:when>
                                <xsl:otherwise>
                                    <data field="first_name"><xsl:value-of select="$first"/></data>
                                    <data field="last_name"><xsl:value-of select="substring-after($ContactName, ' ')"/></data>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <data field="first_name"><xsl:value-of select="$ContactName"/></data>
                        </xsl:otherwise>
                    </xsl:choose>
                    <xsl:if test="$ContactEmail!=''">
                        <resource name="pr_contact">
                            <data field="contact_method">EMAIL</data>
                            <data field="value"><xsl:value-of select="$ContactEmail"/></data>
                        </resource>
                    </xsl:if>
                    <xsl:if test="$ContactPhone!=''">
                        <resource name="pr_contact">
                            <data field="contact_method">WORK_PHONE</data>
                            <data field="value"><xsl:value-of select="$ContactPhone"/></data>
                        </resource>
                    </xsl:if>
                </resource>
            </xsl:if>
        </xsl:if>
        
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_file']">
    
        <xsl:variable name="File" select="data[@field='file']"/>

        <resource name="doc_document">
            <xsl:attribute name="tuid">
                <xsl:value-of select="substring-after($File, '/download/')"/>
            </xsl:attribute>
            <reference field="doc_id" resource="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="reference[field='project_id']/@uuid"/>
                </xsl:attribute>
                <data field="file">
                    <xsl:attribute name="filename">
                        <xsl:value-of select="concat('doc_document', substring-after($File, '/download/drrpp_file'))"/>
                    </xsl:attribute>
                    <xsl:attribute name="url">
                        <xsl:text>local</xsl:text>
                    </xsl:attribute>
                </data>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_framework_file']">

        <xsl:variable name="File" select="data[@field='file']"/>

        <resource name="doc_document">
            <xsl:attribute name="tuid">
                <xsl:value-of select="substring-after($File, '/download/')"/>
            </xsl:attribute>
            <reference field="doc_id" resource="project_framework">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="reference[field='framework_id']/@uuid"/>
                </xsl:attribute>
                <data field="file">
                    <xsl:attribute name="filename">
                        <xsl:value-of select="concat('doc_document', substring-after($File, '/download/drrpp_file'))"/>
                    </xsl:attribute>
                    <xsl:attribute name="url">
                        <xsl:text>local</xsl:text>
                    </xsl:attribute>
                </data>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_framework']">

        <resource name="project_framework">

            <xsl:attribute name="tuid">
                <xsl:value-of select="@uuid"/>
            </xsl:attribute>
            <xsl:attribute name="created_on">
                <xsl:value-of select="@created_on"/>
            </xsl:attribute>
            <xsl:attribute name="modified_on">
                <xsl:value-of select="@modified_on"/>
            </xsl:attribute>
            <xsl:attribute name="created_by">
                <xsl:value-of select="@created_by"/>
            </xsl:attribute>
            <xsl:attribute name="modified_by">
                <xsl:value-of select="@modified_by"/>
            </xsl:attribute>

            <xsl:if test="data[@field='approved']='True'">
                <xsl:attribute name="approved_by">
                    <xsl:value-of select="@modified_by"/>
                </xsl:attribute>
            </xsl:if>

            <data field="name"><xsl:value-of select="data[@field='name']"/></data>
            <data field="description"><xsl:value-of select="data[@field='description']"/></data>
            <data field="time_frame"><xsl:value-of select="data[@field='time_frame']"/></data>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='file_dummy']"/></xsl:with-param>
                <xsl:with-param name="arg">file</xsl:with-param>
            </xsl:call-template>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_group']">

        <xsl:variable name="OrgName" select="data[@field='name']"/>
        <xsl:variable name="OrgType" select="data[@field='type']/@value"/>

        <resource name="org_organisation">
            <data field="name"><xsl:value-of select="$OrgName"/></data>
            <data field="acronym"><xsl:value-of select="data[@field='acronym']"/></data>
            <data field="year"><xsl:value-of select="data[@field='year']"/></data>
            <data field="comments"><xsl:value-of select="data[@field='notes']"/></data>

            <reference field="organisation_type_id" resource="org_organisation_type">
                <xsl:choose>
                    <xsl:when test="$OrgType=5">
                        <xsl:attribute name="tuid">OrgType:Network</xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:attribute name="tuid">OrgType:Committees/Mechanism/Forum</xsl:attribute>
                    </xsl:otherwise>
                </xsl:choose>
            </reference>

            <resource name="org_office">
                <xsl:choose>
                    <xsl:when test="string-length($OrgName) &gt; 64">
                        <data field="name"><xsl:value-of select="substring($OrgName, 0, 64)"/></data>
                    </xsl:when>
                    <xsl:otherwise>
                        <data field="name"><xsl:value-of select="$OrgName"/></data>
                    </xsl:otherwise>
                </xsl:choose>
                <reference field="location_id" resource="gis_location">
                    <data field="addr_street"><xsl:value-of select="data[@field='location']"/></data>
                </reference>
            </resource>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_link']">

        <xsl:variable name="URL" select="data[@field='url']"/>

        <resource name="doc_document">
            <reference field="doc_id" resource="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="reference[field='project_id']/@uuid"/>
                </xsl:attribute>
            </reference>
            <xsl:choose>
                <xsl:when test="string-length($URL) &gt; 128">
                    <data field="name"><xsl:value-of select="substring($URL, 0, 128)"/></data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="name"><xsl:value-of select="$URL"/></data>
                </xsl:otherwise>
            </xsl:choose>
            <data field="url"><xsl:value-of select="translate($URL, ' ', '')"/></data>
            <data field="comments"><xsl:value-of select="data[@field='comment']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_organisation']">

        <xsl:variable name="OrgName" select="data[@field='name']"/>
        <xsl:variable name="OrgType" select="data[@field='type']/@value"/>

        <resource name="org_organisation">
            <data field="name"><xsl:value-of select="$OrgName"/></data>
            <data field="acronym"><xsl:value-of select="data[@field='acronym']"/></data>
            <data field="website"><xsl:value-of select="data[@field='website']"/></data>
            <data field="year"><xsl:value-of select="data[@field='year']"/></data>
            <data field="comments"><xsl:value-of select="data[@field='notes']"/></data>
            <data field="region"><xsl:value-of select="reference[@field='country_id']"/></data>

            <reference field="organisation_type_id" resource="org_organisation_type">
                <xsl:choose>
                    <xsl:when test="$OrgType=1">
                        <xsl:attribute name="tuid">OrgType:Regional Office</xsl:attribute>
                    </xsl:when>
                    <xsl:when test="$OrgType=2">
                        <xsl:attribute name="tuid">OrgType:Regional Organisation</xsl:attribute>
                    </xsl:when>
                    <xsl:when test="$OrgType=3">
                        <xsl:attribute name="tuid">OrgType:Regional Center</xsl:attribute>
                    </xsl:when>
                </xsl:choose>
            </reference>

            <resource name="org_office">
                <xsl:choose>
                    <xsl:when test="string-length($OrgName) &gt; 64">
                        <data field="name"><xsl:value-of select="substring($OrgName, 0, 64)"/></data>
                    </xsl:when>
                    <xsl:otherwise>
                        <data field="name"><xsl:value-of select="$OrgName"/></data>
                    </xsl:otherwise>
                </xsl:choose>
                <reference field="location_id" resource="gis_location">
                    <data field="addr_street"><xsl:value-of select="data[@field='location']"/></data>
                </reference>
            </resource>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_output']">

        <resource name="project_output">
            <data field="name"><xsl:value-of select="data[@field='output']"/></data>
            <xsl:choose>
                <xsl:when test="data[@field='status']='Proposed'">
                    <data field="status">1</data>
                </xsl:when>
                <xsl:when test="data[@field='status']='Achieved'">
                    <data field="status">2</data>
                </xsl:when>
            </xsl:choose>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='org_organisation']">

        <xsl:variable name="Country" select="reference[@field='country_id']"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="@uuid"/>
            </xsl:attribute>
            <xsl:attribute name="created_on">
                <xsl:value-of select="@created_on"/>
            </xsl:attribute>
            <xsl:attribute name="modified_on">
                <xsl:value-of select="@modified_on"/>
            </xsl:attribute>
            <xsl:attribute name="created_by">
                <xsl:value-of select="@created_by"/>
            </xsl:attribute>
            <xsl:attribute name="modified_by">
                <xsl:value-of select="@modified_by"/>
            </xsl:attribute>

            <xsl:if test="data[@field='approved']='True'">
                <xsl:attribute name="approved_by">
                    <xsl:value-of select="@modified_by"/>
                </xsl:attribute>
            </xsl:if>

            <data field="name"><xsl:value-of select="data[@field='name']"/></data>
            <data field="acronym"><xsl:value-of select="data[@field='acronym']"/></data>
            <data field="website"><xsl:value-of select="data[@field='website']"/></data>
            <data field="year"><xsl:value-of select="data[@field='year']"/></data>
            <data field="comments"><xsl:value-of select="data[@field='notes']"/></data>

            <xsl:if test="$Country!='' and $Country!='International'">
                <!-- Country Code = UUID of the L0 Location -->
                <xsl:variable name="countrycode">
                    <xsl:call-template name="countryname2iso">
                        <xsl:with-param name="country">
                            <xsl:value-of select="$Country"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <data field="country"><xsl:value-of select="$countrycode"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_person']">

        <xsl:variable name="first_name" select="data[@field='first_name']"/>
        <xsl:variable name="last_name" select="data[@field='last_name']"/>

        <xsl:if test="$first_name!=$last_name and $first_name!='Test' and $last_name!='Test' and $first_name!='test' and $last_name!='test'">
            <resource name="pr_person">
                <data field="first_name"><xsl:value-of select="$first_name"/></data>
                <data field="last_name"><xsl:value-of select="$last_name"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='auth_user']">

        <xsl:variable name="first_name" select="data[@field='first_name']"/>
        <xsl:variable name="last_name" select="data[@field='last_name']"/>
        <xsl:variable name="registration_key" select="data[@field='registration_key']"/>
        <xsl:variable name="position" select="data[@field='position']"/>
        <xsl:variable name="reason" select="data[@field='reason']"/>
        <xsl:variable name="organisation">
            <xsl:value-of select="reference[@field='organisation_id']"/>
        </xsl:variable>

        <xsl:if test="$first_name!=$last_name and $first_name!='Test' and $last_name!='Test' and $first_name!='test' and $last_name!='test'">
            <resource name="auth_user">
                <data field="first_name"><xsl:value-of select="$first_name"/></data>
                <data field="last_name"><xsl:value-of select="$last_name"/></data>
                <data field="email"><xsl:value-of select="data[@field='email']"/></data>
                <data field="password"><xsl:value-of select="data[@field='password']"/></data>
                <xsl:if test="$registration_key!=''">
                    <data field="registration_key"><xsl:value-of select="$registration_key"/></data>
                </xsl:if>
                <xsl:if test="$reason!=''">
                    <data field="comments">
                        <xsl:value-of select="concat($position, ' | ', $reason)"/>
                    </data>
                </xsl:if>
                <!-- NB This requires a custom onvalidation to lookup the org to convert to integer-->
                <xsl:if test="$organisation!=''">
                    <data field="organisation_id"><xsl:value-of select="$organisation"/></data>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>

            <!-- Country reference list -->
            <xsl:when test="$arg='countrycode'">
                <xsl:variable name="CountryCode">
                    <xsl:choose>
                        <xsl:when test="string-length($item)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$item"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$item"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:value-of select="concat(',&quot;', 'urn:iso:std:iso:3166:-1:code:', $CountryCode, '&quot;')"/>
            </xsl:when>

            <!-- Hazard list -->
            <xsl:when test="$arg='hazard'">
                <resource name="project_hazard">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($HazardPrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>

            <!-- Theme list -->
            <xsl:when test="$arg='theme'">
                <resource name="project_theme">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($ThemePrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>

            <!-- Partner Organisations -->
            <xsl:when test="$arg='impl_org'">
                <resource name="project_organisation">
                    <data field="role">2</data>
                    <resource name="org_organisation">
                        <data field="name"><xsl:value-of select="$item"/></data>
                    </resource>
                </resource>
            </xsl:when>

            <!-- Donors -->
            <xsl:when test="$arg='donor'">
                <resource name="project_organisation">
                    <data field="role">3</data>
                    <resource name="org_organisation">
                        <data field="name"><xsl:value-of select="$item"/></data>
                    </resource>
                </resource>
            </xsl:when>

            <!-- Outputs -->
            <xsl:when test="$arg='output'">
                <resource name="project_output">
                    <data field="name"><xsl:value-of select="$item"/></data>
                    <reference field="project_id" resource="project_project">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="reference[@field='project_id']/@uuid"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>

            <!-- Files -->
            <xsl:when test="$arg='file'">
                <resource name="doc_document">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="substring-before($item, ';')"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="substring-after($item, ';')"/></data>
                    <data field="file">
                        <xsl:attribute name="filename">
                            <xsl:value-of select="concat('doc_document', substring-after(substring-before($item, ';'), 'drrpp_file'))"/>
                        </xsl:attribute>
                        <xsl:attribute name="url">
                            <xsl:text>local</xsl:text>
                        </xsl:attribute>
                    </data>
                </resource>
            </xsl:when>

            <!-- Links -->
            <xsl:when test="$arg='link'">
                <resource name="doc_document">
                    <xsl:choose>
                        <xsl:when test="string-length($item) &gt; 128">
                            <data field="name"><xsl:value-of select="substring($item, 0, 128)"/></data>
                        </xsl:when>
                        <xsl:otherwise>
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </xsl:otherwise>
                    </xsl:choose>
                    <data field="url"><xsl:value-of select="translate($item, ' ', '')"/></data>
                </resource>
            </xsl:when>

        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
