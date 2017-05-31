<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Users - CSV Import Stylesheet

         CSV fields:
         First Name..............auth_user.first_name
         Last Name...............auth_user.last_name (Can also call the column Middle Name to allow Hispanic names to be used across both hrm/person & auth_user)
         Email...................auth_user.email
         Password................auth_user.password
         Language................auth_user.language
         Role....................auth_group.role
         Organisation...................required.....organisation name
         Branch.........................optional.....branch organisation name
         ...SubBranch,SubSubBranch...etc (indefinite depth, must specify all from root)

         Link....................auth_user.link_user_to (=> human_resource.type)L Staff, Volunteer or Member
         Facility Type...........s3db[tablename]
         Office..................org_site.name
         Organisation Group......org_group.name

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="OrgGroupHeaders">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">OrgGroup</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->

    <xsl:key name="groups" match="row"
             use="col[contains(document('../labels.xml')/labels/column[@name='OrgGroup']/match/text(),
                               concat('|', @field, '|'))]"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Import the Organisation hierarchy -->
            <xsl:for-each select="table/row[1]">
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="level">Organisation</xsl:with-param>
                    <xsl:with-param name="rows" select="//table/row"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Org Groups -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orggroups',
                                            col[contains(document('../labels.xml')/labels/column[@name='OrgGroup']/match/text(),
                                                         concat('|', @field, '|'))])[1])]">
                <xsl:call-template name="OrgGroup">
                    <xsl:with-param name="Field" select="$OrgGroupHeaders"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="GroupName" select="col[@field='Organisation Group']/text()"/>
        <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="Link" select="col[@field='Link']/text()"/>

        <!-- Create the User -->
        <resource name="auth_user">
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <xsl:choose>
                <xsl:when test="col[@field='Last Name']!=''">
                    <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
                </xsl:when>
                <xsl:when test="col[@field='Middle Name']!=''">
                    <!-- Apellido Paterno -->
                    <data field="last_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
                </xsl:when>
            </xsl:choose>
            <data field="email"><xsl:value-of select="col[@field='Email']"/></data>
            <data field="password">
                <xsl:attribute name="value">
                    <xsl:value-of select="col[@field='Password']"/>
                </xsl:attribute>
            </data>
            <xsl:if test="col[@field='Language']!=''">
                <data field="language"><xsl:value-of select="col[@field='Language']"/></data>
            </xsl:if>
            <xsl:if test="$Link!=''">
                <data field="link_user_to">
                    <xsl:call-template name="lowercase">
                        <xsl:with-param name="string">
                           <xsl:value-of select="$Link"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </data>
            </xsl:if>

            <!-- Add other roles as per list -->
            <xsl:variable name="roles" select="col[@field='Role']/text()"/>
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$roles"/>
            </xsl:call-template>

            <!-- Link to Organisation -->
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Site -->
            <xsl:if test="$OfficeName!=''">
                <xsl:variable name="resourcename">
                    <xsl:choose>
                        <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                        <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                        <xsl:when test="$FacilityType='Fire Station'">fire_station</xsl:when>
                        <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                        <xsl:when test="$FacilityType='Police Station'">police_station</xsl:when>
                        <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                        <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                        <xsl:otherwise>org_office</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <reference field="site_id">
                    <xsl:attribute name="resource">
                        <xsl:value-of select="$resourcename"/>
                    </xsl:attribute>
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID">
                            <xsl:with-param name="prefix">OFFICE:</xsl:with-param>
                            <xsl:with-param name="suffix" select="concat('/', $OfficeName)"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Organisation Group -->
            <xsl:if test="$GroupName!=''">
                <reference field="org_group_id" resource="org_group">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('OrgGroup:', $GroupName)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template to import the Organisation hierarchy, to be called only once for the first row -->

    <xsl:template name="OrganisationHierarchy">

        <xsl:param name="level"/>
        <xsl:param name="rows"/>
        <xsl:param name="parentID"/>

        <!-- Get the next level -->
        <xsl:variable name="nextLevel">
            <xsl:call-template name="NextLevel">
                <xsl:with-param name="level" select="$level"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- Get the name -->
        <xsl:variable name="name" select="col[@field=$level]/text()"/>

        <!-- Generate the tuid -->
        <xsl:variable name="tuid">
            <xsl:choose>
                <xsl:when test="$parentID and $parentID!=''">
                    <xsl:value-of select="concat($parentID, '/', $name)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="concat('ORG:', $name)"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Create this Organisation -->
        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$name"/></data>
            <xsl:if test="$parentID and $parentID!=''">
                <resource name="org_organisation_branch" alias="parent">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$parentID"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </resource>

        <!-- Create all offices for this organisation -->
        <xsl:for-each select="$rows[col[@field=$level]/text()=$name and
                                    (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                    col[@field='Office']/text()!='']">

            <xsl:variable name="OfficeName" select="col[@field='Office']"/>
            <xsl:if test="generate-id(.)=generate-id($rows[col[@field=$level]/text()=$name and
                                                           (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                                           col[@field='Office']/text()=$OfficeName][1])">
                <xsl:call-template name="Office"/>
            </xsl:if>
        </xsl:for-each>

        <!-- Process Branches -->
        <xsl:for-each select="$rows[col[@field=$level]/text()=$name and col[@field=$nextLevel]/text()!=''][1]">
            <xsl:call-template name="OrganisationHierarchy">
                <xsl:with-param name="rows" select="$rows[col[@field=$level]/text()=$name and col[@field=$nextLevel]/text()!='']"/>
                <xsl:with-param name="level" select="$nextLevel"/>
                <xsl:with-param name="parentID" select="$tuid"/>
            </xsl:call-template>
        </xsl:for-each>

        <!-- Process Siblings -->
        <xsl:for-each select="$rows[col[@field=$level]/text()!=$name][1]">
            <xsl:call-template name="OrganisationHierarchy">
                <xsl:with-param name="rows" select="$rows[col[@field=$level]/text()!=$name]"/>
                <xsl:with-param name="level" select="$level"/>
                <xsl:with-param name="parentID" select="$parentID"/>
            </xsl:call-template>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template to generate an organisation tuid for the current row -->

    <xsl:template name="OrganisationID">

        <xsl:param name="parentID"/>
        <xsl:param name="parentLevel"/>
        <xsl:param name="prefix">ORG:</xsl:param>
        <xsl:param name="suffix"/>

        <xsl:variable name="level">
            <xsl:call-template name="NextLevel">
                <xsl:with-param name="level" select="$parentLevel"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="name" select="col[@field=$level]/text()"/>
        <xsl:choose>
            <xsl:when test="$name!=''">
                <xsl:variable name="id">
                    <xsl:choose>
                        <xsl:when test="$parentID and $parentID!=''">
                            <xsl:value-of select="concat($parentID, '/', $name)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="concat($prefix, $name)"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:call-template name="OrganisationID">
                    <xsl:with-param name="parentID" select="$id"/>
                    <xsl:with-param name="parentLevel" select="$level"/>
                    <xsl:with-param name="prefix" select="$prefix"/>
                    <xsl:with-param name="suffix" select="$suffix"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat($parentID, $suffix)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template to generate the name of the next level column -->

    <xsl:template name="NextLevel">

        <xsl:param name="level"/>
        <xsl:choose>
            <xsl:when test="not($level) or $level=''">Organisation</xsl:when>
            <xsl:when test="$level='Organisation'">Branch</xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat('Sub', $level)"/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Office">

        <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Fire Station'">fire_station</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Police Station'">police_station</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="$OfficeName!=''">
            <resource>
                <xsl:attribute name="name">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:call-template name="OrganisationID">
                        <xsl:with-param name="prefix">OFFICE:</xsl:with-param>
                        <xsl:with-param name="suffix" select="concat('/', $OfficeName)"/>
                    </xsl:call-template>
                </xsl:attribute>

                <!-- Name field is limited to 64 chars -->
                <data field="name"><xsl:value-of select="substring($OfficeName,1,64)"/></data>

                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>

        <xsl:variable name="role">
            <xsl:choose>
                <xsl:when test="contains($item, '/')">
                    <xsl:value-of select="substring-before($item, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$item"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="realm">
            <xsl:choose>
                <xsl:when test="contains($item, '/')">
                    <xsl:value-of select="substring-after($item, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'default'"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource name="auth_membership">
            <reference field="group_id" resource="auth_group">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$role"/>
                </xsl:attribute>
            </reference>
            <xsl:choose>
                <xsl:when test="$realm='0'">
                    <data field="pe_id" value="0"/>
                </xsl:when>
                <!-- e.g. org_organisation.name=Viet Nam Red Cross -->
                <xsl:when test="contains($realm, '=')">
                    <data field="pe_id"><xsl:value-of select="$realm"/></data>
                </xsl:when>
            </xsl:choose>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- OrgGroup -->
    <xsl:template name="OrgGroup">

        <xsl:param name="Field">Name</xsl:param>

        <xsl:variable name="Name">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Field"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$Name!=''">
            <resource name="org_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('OrgGroup:', $Name)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
