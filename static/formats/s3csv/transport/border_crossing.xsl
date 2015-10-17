<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
         Border Crossing - CSV Import Stylesheet

         CSV column..................Format.............Content

         Name........................string.............Name
         Comments....................string.............Comments
         Lat.........................optional...........gis_location.lat
         Lon.........................optional...........gis_location.lon
         Countries...................optional...........gis_location.L0 (Comma-separated List of ISO2 codes)

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
            <data field="name">
                <xsl:attribute name="value">
                    <xsl:value-of select="col[@field='Name']"/>
                </xsl:attribute>
            </data>

            <data field="comments">
                <xsl:attribute name="value">
                    <xsl:value-of select="col[@field='Comments']"/>
                </xsl:attribute>
            </data>

            <!-- Location -->
            <xsl:if test="col[@field='Lat']!=''">
                <xsl:call-template name="Location"/>
            </xsl:if>

            <!-- Countries -->
            <xsl:if test="col[@field='Countries']!=''">
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list" select="col[@field='Countries']"/>
                    <xsl:with-param name="arg">country</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

        </resource>
        
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Services -->
            <xsl:when test="$arg='country'">

                <!-- Country Code = UUID of the L0 Location -->
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="string-length($l0)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$arg"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string">
                                   <xsl:value-of select="$arg"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

                <resource name="transport_border_crossing_location">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
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
