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

    <xsl:import href="../orgh.xsl"/>

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

    <!-- END ************************************************************** -->

</xsl:stylesheet>
