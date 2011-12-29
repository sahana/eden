<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
        Sahana Eden XSLT Import Template

        Transformation of
            Ushahidi Incidents (http://wiki.ushahidi.com/doku.php?id=ushahidi_api)
        into
            Sahana Eden Incident Reports
    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:variable name="import_domain">
        <xsl:value-of select="/response/payload/domain/text()"/>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="./response/payload"/>
    </xsl:template>

    <xsl:template match="response/payload">
        <s3xml>
            <xsl:attribute name="domain">
                <xsl:value-of select="$import_domain"/>
            </xsl:attribute>
            <xsl:apply-templates select="./incidents"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="incidents">
            <xsl:for-each select="//incident" >

                <!-- create location 1st so that it can be linked to ticket -->
                <xsl:apply-templates select="./location"/>

                <resource name="irs_ireport">

                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$import_domain"/>
                        <xsl:text>/</xsl:text>
                        <xsl:value-of select="id"/>
                    </xsl:attribute>

                    <data field="name">
                        <xsl:value-of select="title"/>
                    </data>

                    <data field="message">
                        <xsl:value-of select="description"/>
                    </data>

                    <data field="source">
                        <xsl:value-of select="$import_domain"/>
                    </data>

                    <data field="source_id">
                        <xsl:value-of select="id"/>
                    </data>

                    <data field="datetime">
                        <xsl:value-of select="date"/>
                    </data>
                    <!--
                    <data field="">
                        <xsl:value-of select="mode"/>
                    </data>

                    <data field="">
                        <xsl:value-of select="active"/>
                    </data>
                    -->
                    <data field="verified">
                        <xsl:value-of select="verified"/>
                    </data>

                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$import_domain"/>
                            <xsl:text>/</xsl:text>
                            <xsl:value-of select="location/id"/>
                        </xsl:attribute>
                    </reference>

                    <data field="categories">
                        <xsl:choose>

                            <xsl:when test="./id=4"> <!-- 4. Menaces | Security Threats -->
                                <xsl:text>2</xsl:text> <!-- Report Security Incident -->
                            </xsl:when>

                        </xsl:choose>
                    </data>
                </resource>

                <!--
                <xsl:apply-templates select="./categories"/>
                -->

            </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="location">
        <resource name="gis_location">

            <xsl:attribute name="uuid">
                <xsl:value-of select="$import_domain"/>
                <xsl:text>/</xsl:text>
                <xsl:value-of select="id"/>
            </xsl:attribute>

            <data field="gis_feature_type" value="1">Point</data>

            <!-- Ushahidi data is prone to duplicates so we don't want it to clutter other views -->
            <data field="level" value="XX">XX</data>

            <data field="name">
                <xsl:choose>
                    <xsl:when test="./name/text()">
                        <xsl:value-of select="./name/text()"/>
                    </xsl:when>
                    <xsl:when test="./latitude/text() and ./longitude/text()">
                        <xsl:value-of select="concat(./latitude/text(), ',', ./longitude/text())"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>Unnamed location</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <data field="lat">
                <xsl:value-of select="latitude"/>
            </data>

            <data field="lon">
                <xsl:value-of select="longitude"/>
            </data>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="categories">
        <xsl:for-each select="//category">
            <resource name="irs_ireport">
                <!-- id -->
                <data field="name">
                    <xsl:value-of select="title"/>
                </data>
            </resource>
        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>
