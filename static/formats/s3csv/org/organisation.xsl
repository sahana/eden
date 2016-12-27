<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
        Organisation - CSV Import Stylesheet

        CSV fields:
        Organisation............org_organisation (the root organisation name)
        Branch..................org_organisation (the branch name)
        SubBranch...............org_organisation (the sub-branch name)
        SubSubBranch............org_organisation (the sub-sub-branch name)
        ...and so forth (indefinite depth)
            => only specify what applies, leave all subsequent levels empty,
               e.g. the root organisation has only "Organisation", no "Branch"

        Acronym.................org_organisation.acronym
        Name L10n:XX............org_organisation_name.name_10n (Language = XX in column name, name_10n = cell in row. Multiple allowed)
        Acronym L10n:XX.........org_organisation_name.acronym_10n (Language = XX in column name, acronym_10n = cell in row. Multiple allowed)
        Type....................org_organisation$organisation_type_id or org_organisation_type.parent
        SubType.................org_organisation$organisation_type_id or org_organisation_type.parent
        SubSubType..............org_organisation$organisation_type_id
        Sectors.................org_sector_organisation$sector_id
        Services................org_service_organisation$service_id
         OR
        Service.................org_organisation$service_id or org_service.parent
        SubService..............org_organisation$service_id or org_service.parent
        SubSubService...........org_organisation$service_id or org_service.parent
        Groups..................org_group_membership$group_id
        Region..................org_organisation.region_id
        Country.................org_organisation.country (ISO Code)
        Website.................org_organisation.website
        Phone...................org_organisation.phone
        Phone2..................pr_contact.value
        Facebook................pr_contact.value
        Twitter.................pr_contact.value
        Logo....................org_organisation.logo
        KV:XX...................org_organisation_tag Key,Value (Key = XX in column name, value = cell in row. Multiple allowed)
        Comments................org_organisation.comments
        Approved................org_organisation.approved_by
        Realm Entity............org_organisation.realm_entity <- @ToDo

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/countries.xsl"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="OrgTypePrefix" select="'OrgType:'"/>
    <xsl:variable name="ServicePrefix" select="'Service:'"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="region" match="row" use="col[@field='Region']"/>
    <xsl:key name="service" match="row" use="concat(col[@field='Service'], '/',
                                                    col[@field='SubService'], '/',
                                                    col[@field='SubSubService'])"/>
    <xsl:key name="type" match="row" use="concat(col[@field='Type'], '/',
                                                 col[@field='SubType'], '/',
                                                 col[@field='SubSubType'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisation Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type',
                                                                   concat(col[@field='Type'], '/',
                                                                          col[@field='SubType'], '/',
                                                                          col[@field='SubSubType']))[1])]">
                <xsl:call-template name="OrganisationType">
                    <xsl:with-param name="Type">
                         <xsl:value-of select="col[@field='Type']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubType">
                         <xsl:value-of select="col[@field='SubType']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubSubType">
                         <xsl:value-of select="col[@field='SubSubType']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

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
                </xsl:call-template>
            </xsl:for-each>

            <!-- Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('region',
                                                                       col[@field='Region'])[1])]">
                <xsl:call-template name="Region" />
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:call-template name="OrganisationHierarchy">
            <xsl:with-param name="Level">Organisation</xsl:with-param>
            <xsl:with-param name="Subset" select="//row"/>
        </xsl:call-template>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Process the branch hierarchy -->
    <xsl:template name="OrganisationHierarchy">
        <xsl:param name="Parent"/>
        <xsl:param name="ParentPath"/>
        <xsl:param name="Level"/>
        <!-- Subset = all rows with the same parent organisation -->
        <xsl:param name="Subset"/>

        <xsl:variable name="Name" select="col[@field=$Level]"/>
        <xsl:variable name="SubSubset" select="$Subset[col[@field=$Level]/text()=$Name]"/>

        <!-- Construct the branch path (for tuid-generation) -->
        <xsl:variable name="Path">
            <xsl:choose>
                <xsl:when test="$ParentPath!=''">
                    <xsl:value-of select="concat($ParentPath, '/', $Name)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$Name"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Generate the column name of the next level from the current level -->
        <xsl:variable name="NextLevel">
            <xsl:choose>
                <xsl:when test="$Level='Organisation'">Branch</xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="concat('Sub', $Level)"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="col[@field=$NextLevel] and col[@field=$NextLevel]/text()!=''">

                <xsl:if test="generate-id($SubSubset[1])=generate-id(.)">
                    <!-- If the parent organisation of this branch does not exist
                         in the source, then create it now from the bare name -->
                    <xsl:variable name="ParentRow" select="$SubSubset[not(col[@field=$NextLevel]) or
                                                                      not(col[@field=$NextLevel]/text()!='')]"/>
                    <xsl:if test="count($ParentRow)=0">
                        <xsl:call-template name="Organisation">
                            <xsl:with-param name="Name" select="$Name"/>
                            <xsl:with-param name="Path" select="$Path"/>
                            <xsl:with-param name="ParentPath" select="$ParentPath"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:if>

                <!-- Descend one more level down -->
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="Parent" select="$Name"/>
                    <xsl:with-param name="ParentPath" select="$Path"/>
                    <xsl:with-param name="Level" select="$NextLevel"/>
                    <xsl:with-param name="Subset" select="$SubSubset"/>
                </xsl:call-template>

            </xsl:when>
            <xsl:otherwise>

                <!-- Generate the organisation from this row -->
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="Name" select="$Name"/>
                    <xsl:with-param name="Path" select="$Path"/>
                    <xsl:with-param name="ParentPath" select="$ParentPath"/>
                    <xsl:with-param name="Row" select="."/>
                </xsl:call-template>

            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="Name"/>
        <xsl:param name="Path"/>
        <xsl:param name="ParentPath"/>
        <xsl:param name="Row"/>

        <resource name="org_organisation">
            <!-- Use path with prefix to generate the tuid -->
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('ORG:', $Path)"/>
            </xsl:attribute>

            <!-- Add link to parent (if there is one) -->
            <xsl:if test="$ParentPath!=''">
                <resource name="org_organisation_branch" alias="parent">
                    <reference field="organisation_id"  resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('ORG:', $ParentPath)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- All organisations must have a name -->
            <data field="name"><xsl:value-of select="$Name"/></data>

            <xsl:if test="$Row">
                <!-- Use the data in this row -->

                <xsl:variable name="Services" select="col[@field='Services']/text()"/>
                <xsl:variable name="Service">
                    <xsl:value-of select="col[@field='Service']/text()"/>
                </xsl:variable>
                <xsl:variable name="SubService">
                    <xsl:value-of select="col[@field='SubService']/text()"/>
                </xsl:variable>
                <xsl:variable name="SubSubService">
                    <xsl:value-of select="col[@field='SubSubService']/text()"/>
                </xsl:variable>
                <xsl:variable name="Type">
                    <xsl:value-of select="col[@field='Type']/text()"/>
                </xsl:variable>
                <xsl:variable name="SubType">
                    <xsl:value-of select="col[@field='SubType']/text()"/>
                </xsl:variable>
                <xsl:variable name="SubSubType">
                    <xsl:value-of select="col[@field='SubSubType']/text()"/>
                </xsl:variable>

                <xsl:if test="col[@field='Approved']!=''">
                    <data field="approved_by">0</data>
                </xsl:if>

                <xsl:if test="col[@field='Acronym']!=''">
                    <data field="acronym">
                        <xsl:value-of select="col[@field='Acronym']"/>
                    </data>
                </xsl:if>

                <!-- Link to Organisation Type -->
                <xsl:if test="$Type!=''">
                    <resource name="org_organisation_organisation_type">
                        <reference field="organisation_type_id" resource="org_organisation_type">
                            <xsl:attribute name="tuid">
                                <xsl:choose>
                                    <xsl:when test="$SubSubType!=''">
                                        <!-- Hierarchical Type with 3 levels -->
                                        <xsl:value-of select="concat($OrgTypePrefix, $Type, '/', $SubType, '/', $SubSubType)"/>
                                    </xsl:when>
                                    <xsl:when test="$SubType!=''">
                                        <!-- Hierarchical Type with 2 levels -->
                                        <xsl:value-of select="concat($OrgTypePrefix, $Type, '/', $SubType)"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <!-- Simple Type -->
                                        <xsl:value-of select="concat($OrgTypePrefix, $Type)"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- Link to Organisation Service (when Hierarchical + Single per Row) -->
                <xsl:if test="$Service!=''">
                    <resource name="org_service_organisation">
                        <reference field="service_id" resource="org_service">
                            <xsl:attribute name="tuid">
                                <xsl:choose>
                                    <xsl:when test="$SubSubService!=''">
                                        <!-- Hierarchical Service with 3 levels -->
                                        <xsl:value-of select="concat($ServicePrefix, $Service, '/', $SubService, '/', $SubSubService)"/>
                                    </xsl:when>
                                    <xsl:when test="$SubService!=''">
                                        <!-- Hierarchical Service with 2 levels -->
                                        <xsl:value-of select="concat($ServicePrefix, $Service, '/', $SubService)"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <!-- Simple Service -->
                                        <xsl:value-of select="concat($ServicePrefix, $Service)"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <xsl:if test="col[@field='Country']!=''">
                    <xsl:variable name="l0">
                        <xsl:value-of select="col[@field='Country']"/>
                    </xsl:variable>
                    <xsl:variable name="countrycode">
                        <xsl:choose>
                            <xsl:when test="string-length($l0)!=2">
                                <xsl:call-template name="countryname2iso">
                                    <xsl:with-param name="country">
                                        <xsl:value-of select="$l0"/>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$l0"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <data field="country">
                        <xsl:value-of select="$countrycode"/>
                    </data>
                </xsl:if>

                <!-- Link to Region -->
                <xsl:variable name="Region" select="col[@field='Region']/text()"/>
                <xsl:if test="$Region!=''">
                    <reference field="region_id" resource="org_region">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Region:', $Region)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Website -->
                <xsl:variable name="Website" select="col[@field='Website']/text()"/>
                <xsl:if test="$Website!=''">
                    <data field="website">
                        <xsl:value-of select="$Website"/>
                    </data>
                </xsl:if>

                <!-- Email Addresses -->
                <xsl:call-template name="Email">
                    <xsl:with-param name="EmailAddress" select="col[@field='Email']/text()"/>
                </xsl:call-template>

                <!-- Main Phone Number -->
                <xsl:variable name="Phone" select="col[@field='Phone']/text()"/>
                <xsl:if test="$Phone!=''">
                    <data field="phone">
                        <xsl:value-of select="$Phone"/>
                    </data>
                </xsl:if>

                <!-- Alternative Phone Number -->
                <xsl:variable name="Phone2" select="col[@field='Phone2']/text()"/>
                <xsl:if test="$Phone2!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">WORK_PHONE</data>
                        <data field="value">
                            <xsl:value-of select="$Phone2"/>
                        </data>
                    </resource>
                </xsl:if>

                <!-- Facebook -->
                <xsl:variable name="Facebook" select="col[@field='Facebook']/text()"/>
                <xsl:if test="$Facebook!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">FACEBOOK</data>
                        <data field="value">
                            <xsl:value-of select="$Facebook"/>
                        </data>
                    </resource>
                </xsl:if>

                <!-- Twitter -->
                <xsl:variable name="Twitter" select="col[@field='Twitter']/text()"/>
                <xsl:if test="$Twitter!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">TWITTER</data>
                        <data field="value">
                            <xsl:value-of select="$Twitter"/>
                        </data>
                    </resource>
                </xsl:if>

                <!-- Comments -->
                <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
                <xsl:if test="$Comments!=''">
                    <data field="comments">
                        <xsl:value-of select="$Comments"/>
                    </data>
                </xsl:if>

                <!-- L10n -->
                <xsl:for-each select="col[starts-with(@field, 'Name L10n')]">
                    <xsl:variable name="Lang" select="normalize-space(substring-after(@field, ':'))"/>
                    <xsl:variable name="acronym" select="concat('Acronym L10n:', $Lang)"/>
                    <xsl:variable name="Acronym">
                        <xsl:value-of select="../col[@field=$acronym]"/>
                    </xsl:variable>
                    <xsl:call-template name="L10n">
                        <xsl:with-param name="Lang">
                            <xsl:value-of select="$Lang"/>
                        </xsl:with-param>
                        <xsl:with-param name="Acronym">
                            <xsl:value-of select="$Acronym"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>

                <!-- Org Groups -->
                <xsl:variable name="Groups" select="col[@field='Groups']/text()"/>
                <xsl:if test="$Groups!=''">
                    <xsl:call-template name="splitList">
                        <xsl:with-param name="list" select="$Groups"/>
                        <xsl:with-param name="arg">group</xsl:with-param>
                    </xsl:call-template>
                </xsl:if>

                <!-- Sectors -->
                <xsl:variable name="Sectors" select="col[@field='Sectors']/text()"/>
                <xsl:if test="$Sectors!=''">
                    <xsl:call-template name="splitList">
                        <xsl:with-param name="list" select="$Sectors"/>
                        <xsl:with-param name="arg">sector</xsl:with-param>
                    </xsl:call-template>
                </xsl:if>

                <!-- Services(when non-hierarchical + Multi per Row -->
                <xsl:if test="$Services!=''">
                    <xsl:call-template name="splitList">
                        <xsl:with-param name="list" select="$Services"/>
                        <xsl:with-param name="arg">service</xsl:with-param>
                    </xsl:call-template>
                </xsl:if>

                <!-- Logo -->
                <xsl:if test="col[@field='Logo']!=''">
                    <xsl:variable name="logo">
                        <xsl:value-of select="col[@field='Logo']"/>
                    </xsl:variable>
                    <data field="logo">
                        <xsl:attribute name="url">
                            <xsl:value-of select="$logo"/>
                        </xsl:attribute>
                        <!--
                        <xsl:attribute name="filename">
                            <xsl:call-template name="substringAfterLast">
                                <xsl:with-param name="input" select="$logo"/>
                                <xsl:with-param name="sep" select="'/'"/>
                            </xsl:call-template>
                        </xsl:attribute>-->
                    </data>
                </xsl:if>

                <!-- Arbitrary Tags -->
                <xsl:for-each select="col[starts-with(@field, 'KV')]">
                    <xsl:call-template name="KeyValue"/>
                </xsl:for-each>

            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <!-- @ToDo
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$Value"/>
                <xsl:with-param name="arg">tag</xsl:with-param>
            </xsl:call-template> -->
            <resource name="org_organisation_tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L10n">
        <xsl:param name="Acronym"/>
        <xsl:param name="Lang"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="org_organisation_name">
                <data field="language"><xsl:value-of select="$Lang"/></data>
                <data field="name_l10n"><xsl:value-of select="$Value"/></data>
                <data field="acronym_l10n">
                    <xsl:value-of select="$Acronym"/>
                </data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrganisationService">
        <xsl:param name="Service"/>
        <xsl:param name="SubService"/>
        <xsl:param name="SubSubService"/>

        <!-- @todo: migrate to Taxonomy-pattern, see vulnerability/data.xsl -->
        <resource name="org_service">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($ServicePrefix, $Service)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Service"/></data>
        </resource>
        <xsl:if test="$SubService!=''">
            <resource name="org_service">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ServicePrefix, $Service, '/', $SubService)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$SubService"/></data>
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
                <reference field="parent" resource="org_service">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($ServicePrefix, $Service, '/', $SubService)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrganisationType">
        <xsl:param name="Type"/>
        <xsl:param name="SubType"/>
        <xsl:param name="SubSubType"/>

        <!-- @todo: migrate to Taxonomy-pattern, see vulnerability/data.xsl -->
        <xsl:if test="$Type!=''">
            <resource name="org_organisation_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($OrgTypePrefix, $Type)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Type"/></data>
            </resource>
            <xsl:if test="$SubType!=''">
                <resource name="org_organisation_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($OrgTypePrefix, $Type, '/', $SubType)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$SubType"/></data>
                    <reference field="parent" resource="org_organisation_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgTypePrefix, $Type)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
            <xsl:if test="$SubSubType!=''">
                <resource name="org_organisation_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($OrgTypePrefix, $Type, '/', $SubType, '/', $SubSubType)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$SubSubType"/></data>
                    <reference field="parent" resource="org_organisation_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgTypePrefix, $Type, '/', $SubType)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Region">
        <xsl:if test="col[@field='Region']!=''">
            <resource name="org_region">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Region:', col[@field='Region'])"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="col[@field='Region']"/>
                </data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Email">

        <xsl:param name="EmailAddress"/>

        <xsl:variable name="head" select="substring-before($EmailAddress, ',')"/>
        <xsl:variable name="tail" select="substring-after($EmailAddress, ',')"/>

        <xsl:variable name="value">
            <xsl:choose>
                <xsl:when test="contains($EmailAddress, ',')">
                    <xsl:value-of select="normalize-space($head)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="normalize-space($EmailAddress)"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$value!=''">
            <resource name="pr_contact">
                <data field="contact_method">EMAIL</data>
                <data field="value">
                    <xsl:value-of select="$value"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="Email">
                <xsl:with-param name="EmailAddress" select="$tail"/>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Org Groups -->
            <xsl:when test="$arg='group'">
                <resource name="org_group_membership">
                    <reference field="group_id" resource="org_group">
                        <resource name="org_group">
                            <data field="name">
                                <xsl:value-of select="$item"/>
                            </data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
            <!-- Sectors -->
            <xsl:when test="$arg='sector'">
                <resource name="org_sector_organisation">
                    <reference field="sector_id" resource="org_sector">
                        <resource name="org_sector">
                            <data field="abrv">
                                <xsl:value-of select="$item"/>
                            </data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
            <!-- Services -->
            <xsl:when test="$arg='service'">
                <resource name="org_service_organisation">
                    <reference field="service_id" resource="org_service">
                        <resource name="org_service">
                            <data field="name">
                                <xsl:value-of select="$item"/>
                            </data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <xsl:template name="quote"/>

    <!-- END ************************************************************** -->
</xsl:stylesheet>
