<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         BR Need Types - CSV Import Stylesheet

         CSV column..................Format..........Content

         uuid........................string..........Need.uuid (Not currently supported for Hierarchical Types)
         Organisation................string..........Organisation Name
         Branch.........................optional.....Organisation Branch Name
         ...SubBranch,SubSubBranch...etc (indefinite depth, must specify all from root)

         Type........................string..........Type Name
         SubType.....................string..........Sub Type Name
         SubSubType... (indefinite depth)

         Protection..................string..........is a protection need type
                                                     (true|false)
         Comments....................string..........Comments

    *********************************************************************** -->
    <xsl:import href="../orgh.xsl"/>

    <xsl:output method="xml"/>

    <xsl:key name="services" match="row" use="col[@field='Service']"/>

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

            <!-- Need Types -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:call-template name="TypeHierarchy">
            <xsl:with-param name="Level">Type</xsl:with-param>
            <xsl:with-param name="Subset" select="//row"/>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Process the type hierarchy -->

    <xsl:template name="TypeHierarchy">
        <xsl:param name="Parent"/>
        <xsl:param name="ParentPath"/>
        <xsl:param name="Level"/>
        <xsl:param name="Subset"/>

        <xsl:variable name="Name" select="col[@field=$Level]"/>
        <test><xsl:value-of select="$Name"/></test>

        <xsl:if test="$Name!=''">

            <xsl:variable name="SubSubset" select="$Subset[col[@field=$Level]/text()=$Name]"/>

            <!-- Construct the path (for tuid-generation) -->
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
                    <xsl:when test="$Level='Type'">SubType</xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat('Sub', $Level)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:choose>
                <xsl:when test="col[@field=$NextLevel] and col[@field=$NextLevel]/text()!=''">

                    <xsl:if test="generate-id($SubSubset[1])=generate-id(.)">
                        <!-- If the parent type does not exist in the source,
                            then create it now from the bare name -->
                        <xsl:variable name="ParentRow" select="$SubSubset[not(col[@field=$NextLevel]) or
                                                                        not(col[@field=$NextLevel]/text()!='')]"/>
                        <xsl:if test="count($ParentRow)=0">
                            <xsl:call-template name="NeedType">
                                <xsl:with-param name="Name" select="$Name"/>
                                <xsl:with-param name="Path" select="$Path"/>
                                <xsl:with-param name="ParentPath" select="$ParentPath"/>
                            </xsl:call-template>
                        </xsl:if>
                    </xsl:if>

                    <!-- Descend one more level down -->
                    <xsl:call-template name="TypeHierarchy">
                        <xsl:with-param name="Parent" select="$Name"/>
                        <xsl:with-param name="ParentPath" select="$Path"/>
                        <xsl:with-param name="Level" select="$NextLevel"/>
                        <xsl:with-param name="Subset" select="$SubSubset"/>
                    </xsl:call-template>

                </xsl:when>
                <xsl:otherwise>

                    <!-- Generate the type from this row -->
                    <xsl:call-template name="NeedType">
                        <xsl:with-param name="Name" select="$Name"/>
                        <xsl:with-param name="Path" select="$Path"/>
                        <xsl:with-param name="ParentPath" select="$ParentPath"/>
                        <xsl:with-param name="Row" select="."/>
                    </xsl:call-template>

                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="NeedType">
        <xsl:param name="Name"/>
        <xsl:param name="Path"/>
        <xsl:param name="ParentPath"/>
        <xsl:param name="Row"/>

        <xsl:variable name="uuid" select="col[@field='uuid']"/>

        <resource name="br_need">
            <xsl:choose>
                <xsl:when test="$uuid!=''">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$uuid"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Use path with prefix to generate the tuid -->
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('TYPE:', $Path)"/>
                    </xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Add link to parent (if there is one) -->
            <xsl:if test="$ParentPath!=''">
                <reference field="parent" resource="br_need">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('TYPE:', $ParentPath)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Name -->
            <data field="name"><xsl:value-of select="$Name"/></data>

            <!-- Link to Organisation -->
            <xsl:variable name="Organisation" select="col[@field='Organisation']/text()"/>
            <xsl:if test="$Organisation!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Protection Flag -->
            <xsl:variable name="is_protection" select="col[@field='Protection']/text()"/>
            <data field="protection">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_protection='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <!-- Comments -->
            <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
            <xsl:if test="$Comments!=''">
                <data field="comments">
                    <xsl:value-of select="$Comments"/>
                </data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
