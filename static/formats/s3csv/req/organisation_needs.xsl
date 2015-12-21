<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Organisation Needs - CSV Import Stylesheet

         CSV fields:

         Organisation............org_organisation
         Branch..................org_organisation[_branch]

         Money...................organisation_needs.money_details
         Time....................organisation_needs.vol_details

         Items:Urgent............req_organisation_needs_item
                                 list of items, separated by |
         Items:High..............req_organisation_needs_item
                                 list of items, separated by |
         Items:Moderate..........req_organisation_needs_item
                                 list of items, separated by |
         Items:Low...............req_organisation_needs_item
                                 list of items, separated by |

         Skills:Urgent...........req_organisation_needs_skill
                                 list of skills, separated by |
         Skills:High.............req_organisation_needs_skill
                                 list of skills, separated by |
         Skills:Moderate.........req_organisation_needs_skill
                                 list of skills, separated by |
         Skills:Low..............req_organisation_needs_skill
                                 list of skills, separated by |

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->

    <!-- Organisations and Branches -->
    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="branches" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Create Organisations and Branches -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('branches',
                                                                       concat(col[@field='Organisation'], '/',
                                                                              col[@field='Branch']))[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName">
                        <xsl:value-of select="col[@field='Branch']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Needs -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create Skills -->
        <xsl:call-template name="Skills">
            <xsl:with-param name="list">
                <xsl:value-of select="concat('|', col[@field='Skills:Urgent']/text(),
                                             '|', col[@field='Skills:High']/text(),
                                             '|', col[@field='Skills:Moderate']/text(),
                                             '|', col[@field='Skills:Low']/text(), '|')"/>
            </xsl:with-param>
        </xsl:call-template>

        <!-- Create Items -->
        <xsl:call-template name="Items">
            <xsl:with-param name="list">
                <xsl:value-of select="concat('|', col[@field='Items:Urgent']/text(),
                                             '|', col[@field='Items:High']/text(),
                                             '|', col[@field='Items:Moderate']/text(),
                                             '|', col[@field='Items:Low']/text(), '|')"/>
            </xsl:with-param>
        </xsl:call-template>

        <resource name="req_organisation_needs">

            <!-- Link to Organisation -->
            <xsl:call-template name="OrganisationLink"/>

            <!-- Cash Donations -->
            <data field="money">
                <xsl:choose>
                    <xsl:when test="col[@field='Money']/text()!=''">True</xsl:when>
                    <xsl:otherwise>False</xsl:otherwise>
                </xsl:choose>
            </data>
            <data field="money_details">
                <xsl:value-of select="col[@field='Money']/text()"/>
            </data>

            <!-- Remote Volunteers -->
            <data field="vol">
                <xsl:choose>
                    <xsl:when test="col[@field='Time']/text()!=''">True</xsl:when>
                    <xsl:otherwise>False</xsl:otherwise>
                </xsl:choose>
            </data>
            <data field="vol_details">
                <xsl:value-of select="col[@field='Time']/text()"/>
            </data>

            <!-- Skills needed -->
            <xsl:for-each select="col[starts-with(@field, 'Skills:')]">
                <xsl:call-template name="SkillLinks">
                    <xsl:with-param name="list" select="./text()"/>
                    <xsl:with-param name="demand" select="substring-after(@field, ':')"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Items needed -->
            <xsl:for-each select="col[starts-with(@field, 'Items:')]">
                <xsl:call-template name="ItemLinks">
                    <xsl:with-param name="list" select="./text()"/>
                    <xsl:with-param name="demand" select="substring-after(@field, ':')"/>
                </xsl:call-template>
            </xsl:for-each>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Organisation or Branch (from index) -->

    <xsl:template name="Organisation">

        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <xsl:variable name="tuid">
            <xsl:choose>
                <xsl:when test="$OrgName!='' and $BranchName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName, ':', $BranchName)"/>
                </xsl:when>
                <xsl:when test="$OrgName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName)"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="parent">
            <xsl:if test="$OrgName!='' and $BranchName!='' and $OrgName!=$BranchName">
                <xsl:value-of select="concat('ORG:', $OrgName)"/>
            </xsl:if>
        </xsl:variable>

        <resource name="org_organisation">

            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>

            <data field="name">
                <xsl:choose>
                    <xsl:when test="$BranchName!=''">
                        <xsl:value-of select="$BranchName"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$OrgName"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <xsl:if test="$parent!=''">
                <resource name="org_organisation_branch" alias="parent">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$parent"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Link Needs <=> Organisation -->

    <xsl:template name="OrganisationLink">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>

        <xsl:variable name="tuid">
            <xsl:choose>
                <xsl:when test="$OrgName!='' and $BranchName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName, ':', $BranchName)"/>
                </xsl:when>
                <xsl:when test="$OrgName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName)"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$tuid!=''">
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
            </reference>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Demand">

        <xsl:param name="demand"/>

        <xsl:variable name="demand_opt">
            <xsl:choose>
                <xsl:when test="$demand='Urgent'">4</xsl:when>
                <xsl:when test="$demand='High'">3</xsl:when>
                <xsl:when test="$demand='Moderate'">2</xsl:when>
                <xsl:when test="$demand='Low'">1</xsl:when>
                <xsl:otherwise><xsl:value-of select="$demand"/></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$demand_opt">
            <data field="demand">
                <xsl:value-of select="$demand_opt"/>
            </data>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Skills -->

    <xsl:template name="Skills">

        <xsl:param name="list"/>

        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="contains($list, '|')">
                    <xsl:value-of select="substring-before($list, '|')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$list"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="tail" select="substring-after($list, '|')"/>

        <xsl:if test="$head!='' and
                      not(preceding-sibling::row[contains(concat('|', col[@field='Skills:Urgent'],
                                                                 '|', col[@field='Skills:High'],
                                                                 '|', col[@field='Skills:Moderate'],
                                                                 '|', col[@field='Skills:Low'], '|'), $head)])">
            <resource name="hrm_skill">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('SKILL:', $head)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$head"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="Skills">
                <xsl:with-param name="list">
                    <xsl:value-of select="$tail"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Links Need <=> Skill -->

    <xsl:template name="SkillLinks">

        <xsl:param name="list"/>
        <xsl:param name="demand"/>

        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="contains($list, '|')">
                    <xsl:value-of select="substring-before($list, '|')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$list"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="tail" select="substring-after($list, '|')"/>

        <xsl:if test="$head!=''">
            <resource name="req_organisation_needs_skill">
                <xsl:call-template name="Demand">
                    <xsl:with-param name="demand" select="$demand"/>
                </xsl:call-template>
                <reference field="skill_id" resource="hrm_skill">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('SKILL:', $head)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="SkillLinks">
                <xsl:with-param name="list" select="$tail"/>
                <xsl:with-param name="demand" select="$demand"/>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Items -->

    <xsl:template name="Items">

        <xsl:param name="list"/>

        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="contains($list, '|')">
                    <xsl:value-of select="substring-before($list, '|')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$list"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="tail" select="substring-after($list, '|')"/>

        <xsl:if test="$head!='' and
                      not(preceding-sibling::row[contains(concat('|', col[@field='Items:Urgent'],
                                                                 '|', col[@field='Items:High'],
                                                                 '|', col[@field='Items:Moderate'],
                                                                 '|', col[@field='Items:Low'], '|'), $head)])">
            <resource name="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('ITEM:', $head)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$head"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="Items">
                <xsl:with-param name="list">
                    <xsl:value-of select="$tail"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Links Need <=> Item -->

    <xsl:template name="ItemLinks">

        <xsl:param name="list"/>
        <xsl:param name="demand"/>

        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="contains($list, '|')">
                    <xsl:value-of select="substring-before($list, '|')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$list"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="tail" select="substring-after($list, '|')"/>

        <xsl:if test="$head!=''">
            <resource name="req_organisation_needs_item">
                <xsl:call-template name="Demand">
                    <xsl:with-param name="demand" select="$demand"/>
                </xsl:call-template>
                <reference field="item_id" resource="supply_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('ITEM:', $head)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="ItemLinks">
                <xsl:with-param name="list" select="$tail"/>
                <xsl:with-param name="demand" select="$demand"/>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
