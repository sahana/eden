<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
         Border Crossing - CSV Import Stylesheet

         CSV column..................Format.............Content

         Name........................string.............transport_border_crossing.name
         Comments....................string.............transport_border_crossing.comments
         Status......................string.............transport_border_crossing.status
                                                        OPEN|RESTRICTED|CLOSED
         Lat.........................optional...........gis_location.lat
         Lon.........................optional...........gis_location.lon
         Countries...................optional...........transport_border_crossing_country
                                                        (Comma-separated List of ISO2 codes)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="transport_border_crossing">

            <!-- Name -->
            <data field="name">
                <xsl:attribute name="value">
                    <xsl:value-of select="col[@field='Name']"/>
                </xsl:attribute>
            </data>

            <!-- Location -->
            <xsl:if test="col[@field='Lat']/text()!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:call-template name="Location"/>
                </reference>
                <xsl:call-template name="Location"/>
            </xsl:if>

            <!-- Countries -->
            <xsl:variable name="Countries" select="col[@field='Countries']/text()"/>
            <xsl:if test="$Countries!=''">
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list" select="$Countries"/>
                    <xsl:with-param name="arg">country</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <!-- Status -->
            <xsl:variable name="Status" select="col[@field='Status']/text()"/>
            <xsl:if test="$Status!=''">
                <xsl:variable name="StatusCode">
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                            <xsl:value-of select="$Status"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <data field="status">
                    <xsl:value-of select="$StatusCode"/>
                </data>
            </xsl:if>

            <!-- Comments -->
            <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
            <xsl:if test="$Comments!=''">
                <data field="comments">
                    <xsl:attribute name="value">
                        <xsl:value-of select="col[@field='Comments']"/>
                    </xsl:attribute>
                </data>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>

            <!-- Countries (component of border crossings) -->
            <xsl:when test="$arg='country'">

                <!-- Country Code = UUID of the L0 Location -->
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="string-length($item)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$item"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string">
                                   <xsl:value-of select="$item"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <resource name="transport_border_crossing_country">
                    <data field="country">
                        <xsl:value-of select="$countrycode"/>
                    </data>
                </resource>

            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Location">

        <resource name="gis_location">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
        </resource>

    </xsl:template>

    <!-- END ************************************************************** -->
</xsl:stylesheet>
