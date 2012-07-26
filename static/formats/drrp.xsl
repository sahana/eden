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
        <xsl:for-each select="//resource[@name='drrpp_framework']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_group']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_output']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='drrpp_project']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
        <xsl:for-each select="//resource[@name='org_organisation']">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_project']">

        <xsl:variable name="Countries" select="data[@field='country_dummy']"/>
        <xsl:variable name="LeadOrganisation" select="reference[@field='lead_organisation_id']/@uuid"/>
        <xsl:variable name="ContactOrganisation" select="reference[@field='contact_organisation_id']/@uuid"/>
        <xsl:variable name="ContactName" select="data[@field='contact_name']"/>
        <xsl:variable name="ContactEmail" select="data[@field='contact_email']"/>
        <xsl:variable name="ContactPhone" select="data[@field='contact_phone']"/>

        <resource name="project_project">

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

            <data field="code"><xsl:value-of select="data[@field='short_title']"/></data>
            <data field="name"><xsl:value-of select="data[@field='name']"/></data>
            <data field="description"><xsl:value-of select="data[@field='description']"/></data>
            <data field="start_date"><xsl:value-of select="data[@field='start_date']/@value"/></data>
            <data field="end_date"><xsl:value-of select="data[@field='end_date']/@value"/></data>
            <data field="budget"><xsl:value-of select="data[@field='total_funding']/@value"/></data>
            <data field="currency">USD</data>
            <data field="objectives"><xsl:value-of select="data[@field='objectives']"/></data>
            <data field="comments"><xsl:value-of select="data[@field='comments']"/></data>
            <data field="status"><xsl:value-of select="data[@field='status_id']/@value"/></data>
            <data field="hfa"><xsl:value-of select="data[@field='hfa_ids']/@value"/></data>

            <resource name="project_drrpp">
                <data field="duration"><xsl:value-of select="data[@field='duration']"/></data>
                <data field="outputs"><xsl:value-of select="data[@field='outputs']"/></data>
                <data field="rfa"><xsl:value-of select="data[@field='rfa_ids']/@value"/></data>
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
                <!--<xsl:with-param name="listsep">;</xsl:with-param>-->
                <xsl:with-param name="arg">impl_org</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='funding_dummy']"/></xsl:with-param>
                <!--<xsl:with-param name="listsep">;</xsl:with-param>-->
                <xsl:with-param name="arg">donor</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='output_dummy']"/></xsl:with-param>
                <xsl:with-param name="listsep">;</xsl:with-param>
                <xsl:with-param name="arg">output</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='hazard_ids']"/></xsl:with-param>
                <!--<xsl:with-param name="listsep">;</xsl:with-param>-->
                <xsl:with-param name="arg">hazard</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="data[@field='theme_ids']"/></xsl:with-param>
                <!--<xsl:with-param name="listsep">;</xsl:with-param>-->
                <xsl:with-param name="arg">theme</xsl:with-param>
            </xsl:call-template>

            <!-- Countries -->
            <xsl:if test="$Countries!=''">
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
            </xsl:if>

        </resource>

        <xsl:if test="$ContactOrganisation!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ContactOrganisation"/>
                </xsl:attribute>
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
    <xsl:template match="resource[@name='drrpp_framework']">

        <resource name="project_framework">
            <data field="name"><xsl:value-of select="data[@field='name']"/></data>
            <data field="description"><xsl:value-of select="data[@field='description']"/></data>
            <data field="time_frame"><xsl:value-of select="data[@field='time_frame']"/></data>
            <!-- @ToDo: doc_document -->
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='drrpp_group']">

        <resource name="org_organisation">
            <data field="name"><xsl:value-of select="data[@field='name']"/></data>
            <data field="acronym"><xsl:value-of select="data[@field='acronym']"/></data>
            <data field="year"><xsl:value-of select="data[@field='year']"/></data>
            <data field="comments"><xsl:value-of select="data[@field='notes']"/></data>

            <reference field="organisation_type_id" resource="org_organisation_type">
                <data field="name"><xsl:value-of select="data[@field='type']"/></data>
            </reference>

            <resource name="org_office">
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
                    <reference field="organisation_id" resource="org_organisation">
                        <data field="name"><xsl:value-of select="$item"/></data>
                    </reference>
                </resource>
            </xsl:when>
            <!-- Donors -->
            <xsl:when test="$arg='donor'">
                <resource name="project_organisation">
                    <data field="role">3</data>
                    <reference field="organisation_id" resource="org_organisation">
                        <data field="name"><xsl:value-of select="$item"/></data>
                    </reference>
                </resource>
            </xsl:when>
            <!-- Outputs -->
            <xsl:when test="$arg='output'">
                <resource name="project_output">
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>