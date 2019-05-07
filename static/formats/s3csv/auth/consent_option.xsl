<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         AUTH Consent Options - CSV Import Stylesheet

         CSV column..................Format..........Content

         Code........................string..........Processing Type Code
         Type........................string..........Processing Type Name
         Title.......................string..........Consent Option Title
         Explanation.................text............Explanation of Processing
         Valid From..................date (ISO)......Date when this version becomes valid
         OptOut......................yes|no..........Opt-in by default, explicit opt-out
         Mandatory...................yes|no..........Consent is mandatory for overall
                                                     consent question to succeed
         Comments....................string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="types" match="row" use="col[@field='Code']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Processing Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('types', col[@field='Code'])[1])]">
                <xsl:call-template name="ProcessingType"/>
            </xsl:for-each>

            <!-- Consent Options -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Code" select="normalize-space(col[@field='Code']/text())"/>
        <xsl:variable name="Title" select="normalize-space(col[@field='Title']/text())"/>

        <resource name="auth_consent_option">

            <!-- Processing Type Reference -->
            <reference field="type_id" resource="auth_processing_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('TYPE:', $Code)"/>
                </xsl:attribute>
            </reference>

            <!-- Title and Explanation -->
            <data field="name">
                <xsl:value-of select="$Title"/>
            </data>
            <data field="description">
                <xsl:value-of select="col[@field='Explanation']/text()"/>
            </data>

            <!-- Valid-From Date -->
            <xsl:variable name="valid_from" select="normalize-space(col[@field='Valid From']/text())"/>
            <xsl:if test="$valid_from!=''">
                <data field="valid_from">
                    <xsl:value-of select="$valid_from"/>
                </data>
            </xsl:if>

            <!-- Opt-out -->
            <xsl:variable name="opt_out" select="col[@field='OptOut']/text()"/>
            <data field="opt_out">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$opt_out='yes' or $opt_out='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <!-- Mandatory -->
            <xsl:variable name="mandatory" select="col[@field='Mandatory']/text()"/>
            <data field="mandatory">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$mandatory='yes' or $mandatory='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <!-- Comments -->
            <data field="comments">
                <xsl:value-of select="col[@field='Comments']/text()"/>
            </data>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ProcessingType">

        <xsl:variable name="Code" select="normalize-space(col[@field='Code']/text())"/>
        <xsl:variable name="Name" select="normalize-space(col[@field='Type']/text())"/>

        <resource name="auth_processing_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('TYPE:', $Code)"/>
            </xsl:attribute>
            <data field="code">
                <xsl:value-of select="$Code"/>
            </data>
            <data field="name">
                <xsl:value-of select="$Name"/>
            </data>
        </resource>

    </xsl:template>

    <!-- END ************************************************************** -->

</xsl:stylesheet>
