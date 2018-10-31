<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation hierarchy templates for resources referencing organisations

         - embed with xsl:import at the top of a stylesheet
         - embedding stylesheet is to implement "Office" or "Facility"
           templates if/as needed

         Columns processed by this stylesheet:

         Organisation...................required.....organisation name
         Branch.........................optional.....branch organisation name
         ...SubBranch,SubSubBranch...etc (indefinite depth, must specify all from root)

         These columns are processed if passed as parameter:

         OfficeColumn...................optional.....office name
         FacilityColumn.................optional.....facility name

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Template to import the Organisation Hierarchy, to be called only once for the first row -->

    <xsl:template name="OrganisationHierarchy">

        <xsl:param name="level"/>
        <xsl:param name="rows"/>
        <xsl:param name="parentID"/>
        <xsl:param name="OfficeColumn"/>
        <xsl:param name="FacilityColumn"/>

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
        <xsl:if test="$OfficeColumn!=''">
            <xsl:for-each select="$rows[col[@field=$level]/text()=$name and
                                        (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                        col[@field=$OfficeColumn]/text()!='']">

                <xsl:variable name="OfficeName" select="col[@field=$OfficeColumn]"/>
                <xsl:if test="generate-id(.)=generate-id($rows[col[@field=$level]/text()=$name and
                                                               (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                                               col[@field=$OfficeColumn]/text()=$OfficeName][1])">
                    <xsl:call-template name="Office"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:if>

        <!-- Create all facilities for this organisation -->
        <xsl:if test="$FacilityColumn!=''">
            <xsl:for-each select="$rows[col[@field=$level]/text()=$name and
                                        (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                        col[@field=$FacilityColumn]/text()!='']">

                <xsl:variable name="FacilityName" select="col[@field=$FacilityColumn]"/>
                <xsl:if test="generate-id(.)=generate-id($rows[col[@field=$level]/text()=$name and
                                                               (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                                               col[@field=$FacilityColumn]/text()=$FacilityName][1])">
                    <xsl:call-template name="Facility"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:if>

        <!-- Process Branches -->
        <xsl:for-each select="$rows[col[@field=$level]/text()=$name and col[@field=$nextLevel]/text()!=''][1]">
            <xsl:call-template name="OrganisationHierarchy">
                <xsl:with-param name="rows" select="$rows[col[@field=$level]/text()=$name and col[@field=$nextLevel]/text()!='']"/>
                <xsl:with-param name="level" select="$nextLevel"/>
                <xsl:with-param name="parentID" select="$tuid"/>
                <xsl:with-param name="OfficeColumn" select="$OfficeColumn"/>
                <xsl:with-param name="FacilityColumn" select="$FacilityColumn"/>
            </xsl:call-template>
        </xsl:for-each>

        <!-- Process Siblings -->
        <xsl:for-each select="$rows[col[@field=$level]/text()!=$name][1]">
            <xsl:call-template name="OrganisationHierarchy">
                <xsl:with-param name="rows" select="$rows[col[@field=$level]/text()!=$name]"/>
                <xsl:with-param name="level" select="$level"/>
                <xsl:with-param name="parentID" select="$parentID"/>
                <xsl:with-param name="OfficeColumn" select="$OfficeColumn"/>
                <xsl:with-param name="FacilityColumn" select="$FacilityColumn"/>
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
        <!-- Placeholder, implemented by embedding stylesheet -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Facility">
        <!-- Placeholder, implemented by embedding stylesheet -->
    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>

