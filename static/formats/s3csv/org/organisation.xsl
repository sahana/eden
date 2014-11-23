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
         Comments................org_organisation.comments
         Approved................org_organisation.approved_by

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
        </xsl:call-template>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Process the branch hierarchy -->
    <xsl:template name="OrganisationHierarchy">
        <xsl:param name="Parent"/>
        <xsl:param name="ParentPath"/>
        <xsl:param name="Level"/>

        <xsl:variable name="Name" select="col[@field=$Level]"/>
        
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

                <!-- Descend one more level down -->
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="Parent" select="$Name"/>
                    <xsl:with-param name="ParentPath" select="$Path"/>
                    <xsl:with-param name="Level" select="$NextLevel"/>
                </xsl:call-template>

                <!-- If the parent organisation doesn't exist in this file,
                     create it without row from the bare name -->
                <xsl:if test="not(preceding-sibling::row[col[@field=$Level]/text()=$Name]) and
                              not(../row[col[@field=$Level]/text()=$Name and
                                  (not(col[@field=$NextLevel]) or
                                       col[@field=$NextLevel]/text()='')])">
                    <xsl:call-template name="Organisation">
                        <xsl:with-param name="Name" select="$Name"/>
                        <xsl:with-param name="Path" select="$Path"/>
                        <xsl:with-param name="ParentPath" select="$ParentPath"/>
                    </xsl:call-template>
                </xsl:if>

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
                
                <xsl:variable name="Groups" select="col[@field='Groups']/text()"/>
                <xsl:variable name="Sectors" select="col[@field='Sectors']/text()"/>
                <xsl:variable name="Services" select="col[@field='Services']/text()"/>
                <xsl:variable name="Service">
                    <xsl:value-of select="col[@field='Service']"/>
                </xsl:variable>
                <xsl:variable name="SubService">
                    <xsl:value-of select="col[@field='SubService']"/>
                </xsl:variable>
                <xsl:variable name="SubSubService">
                    <xsl:value-of select="col[@field='SubSubService']"/>
                </xsl:variable>
                <xsl:variable name="Type">
                    <xsl:value-of select="col[@field='Type']"/>
                </xsl:variable>
                <xsl:variable name="SubType">
                    <xsl:value-of select="col[@field='SubType']"/>
                </xsl:variable>
                <xsl:variable name="SubSubType">
                    <xsl:value-of select="col[@field='SubSubType']"/>
                </xsl:variable>

                <xsl:if test="col[@field='Approved']!=''">
                    <data field="approved_by">0</data>
                </xsl:if>
            
                <xsl:if test="col[@field='Acronym']!=''">
                    <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>
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
                
                <xsl:if test="col[@field='Region']!=''">
                    <reference field="region_id" resource="org_region">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Region:', col[@field='Region'])"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                
                <xsl:if test="col[@field='Website']!=''">
                    <data field="website"><xsl:value-of select="col[@field='Website']"/></data>
                </xsl:if>
                
                <xsl:if test="col[@field='Phone']!=''">
                    <data field="phone"><xsl:value-of select="col[@field='Phone']"/></data>
                </xsl:if>
                
                <xsl:if test="col[@field='Phone2']!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">WORK_PHONE</data>
                        <data field="value"><xsl:value-of select="col[@field='Phone2']"/></data>
                    </resource>
                </xsl:if>
                
                <xsl:if test="col[@field='Facebook']!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">FACEBOOK</data>
                        <data field="value"><xsl:value-of select="col[@field='Facebook']"/></data>
                    </resource>
                </xsl:if>
                
                <xsl:if test="col[@field='Twitter']!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">TWITTER</data>
                        <data field="value"><xsl:value-of select="col[@field='Twitter']"/></data>
                    </resource>
                </xsl:if>
                
                <xsl:if test="col[@field='Comments']!=''">
                    <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
                </xsl:if>

                <!-- Org Groups -->
                <xsl:if test="$Groups!=''">
                    <xsl:call-template name="splitList">
                        <xsl:with-param name="list" select="$Groups"/>
                        <xsl:with-param name="arg">group</xsl:with-param>
                    </xsl:call-template>
                </xsl:if>

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
            </xsl:if>
        </resource>

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
                <data field="name"><xsl:value-of select="col[@field='Region']"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Org Groups -->
            <xsl:when test="$arg='grop'">
                <resource name="org_group_membership">
                    <reference field="group_id" resource="org_group">
                        <resource name="org_group">
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
            <!-- Sectors -->
            <xsl:when test="$arg='sector'">
                <resource name="org_sector_organisation">
                    <reference field="sector_id" resource="org_sector">
                        <resource name="org_sector">
                            <data field="abrv"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
            <!-- Services -->
            <xsl:when test="$arg='service'">
                <resource name="org_service_organisation">
                    <reference field="service_id" resource="org_service">
                        <resource name="org_service">
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- END ************************************************************** -->
</xsl:stylesheet>
