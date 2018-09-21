<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         PDF Data Card Configurations - CSV Import Stylesheet

         CSV column..................Format..........Content

         Organisation................string..........Organisation Name
         Branch.........................optional.....Organisation Branch Name
         ...SubBranch,SubSubBranch...etc (indefinite depth, must specify all from root)

         Card Type...................string..........Card Type [VOLID|...]

         Authority Statement.........string..........Card Authority Statement
         Organisation Statement......string..........Org/Affiliation Statement
         Signature Text..............string..........Card Signature Text
         Validity Period.............integer.........Validity Period in Months
         Comments....................string..........Comments

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>

            <!-- Import the organisation hierarchy -->
            <xsl:for-each select="table/row[1]">
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="level">Organisation</xsl:with-param>
                    <xsl:with-param name="rows" select="//table/row"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Process all rows for response themes -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Card Configurations -->
    <xsl:template match="row">

        <xsl:variable name="Type" select="col[@field='Card Type']/text()"/>
        <xsl:if test="$Type!=''">

            <resource name="doc_card_config">

                <!-- Type -->
                <data field="card_type">
                    <xsl:value-of select="$Type"/>
                </data>

                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>

                <!-- Card Texts -->
                <data field="authority_statement">
                    <xsl:value-of select="col[@field='Authority Statement']/text()"/>
                </data>
                <data field="org_statement">
                    <xsl:value-of select="col[@field='Organisation Statement']/text()"/>
                </data>
                <data field="signature_text">
                    <xsl:value-of select="col[@field='Signature Text']/text()"/>
                </data>

                <!-- Validity Period -->
                <data field="validity_period">
                    <xsl:value-of select="col[@field='Validity Period']/text()"/>
                </data>

                <!-- Comments -->
                <data field="comments">
                    <xsl:value-of select="col[@field='comments']"/>
                </data>

            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template to import the organisation hierarchy, to be called only once for the first row -->

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

    <!-- END ************************************************************** -->

</xsl:stylesheet>
