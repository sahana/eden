<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Document node -->
    <xsl:template match="/">
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Root element -->
    <xsl:template match="s3xml">
        <CoronaWWS>
            <xsl:apply-templates select="resource[@name='req_req']"/>
        </CoronaWWS>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Request -->
    <xsl:template match="resource[@name='req_req']">

        <xsl:variable name="SiteUUID" select="reference[@field='site_id']/@uuid"/>
        <xsl:variable name="SiteType" select="reference[@field='site_id']/@resource"/>
        <xsl:variable name="Site" select="//resource[@name=$SiteType and @uuid=$SiteUUID]"/>

        <xsl:if test="$Site">
            <Bestellung>
                <!-- Requester Information -->
                <xsl:call-template name="Requester">
                    <xsl:with-param name="Site" select="$Site"/>
                </xsl:call-template>

                <!-- Request Reference (not yet specified) -->
                <ReferenzNr>
                    <xsl:value-of select="data[@field='req_ref']/text()"/>
                </ReferenzNr>

                <!-- Request date, using local format DD.MM.YYYY rather than ISO-Format -->
                <Bestelldatum>
                    <xsl:value-of select="substring-before(data[@field='date']/text(), ' ')"/>
                </Bestelldatum>

                <!-- Request comments -->
                <Anmerkungen>
                    <xsl:value-of select="data[@field='comments']/text()"/>
                </Anmerkungen>

                <!-- This is repeated in the <Besteller> element -->
                <Email>
                    <xsl:value-of select="$Site/data[@field='email']/text()"/>
                </Email>

                <!-- The requested items -->
                <xsl:apply-templates select="resource[@name='req_req_item']"/>

            </Bestellung>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Request Item -->
    <xsl:template match="resource[@name='req_req_item']">
        <xsl:variable name="ItemUUID" select="reference[@field='item_id']/@uuid"/>
        <xsl:variable name="PackUUID" select="reference[@field='item_pack_id']/@uuid"/>
        <xsl:variable name="Quantity" select="data[@field='quantity']/@value"/>

        <xsl:if test="$ItemUUID!='' and $PackUUID!='' and $Quantity!=''">

            <xsl:variable name="ItemCode" select="//resource[@name='supply_item' and @uuid=$ItemUUID]/data[@field='code']/text()"/>
            <xsl:variable name="PackQuantity" select="//resource[@name='supply_item_pack' and @uuid=$PackUUID]/data[@field='quantity']/@value"/>

            <xsl:if test="$ItemCode!='' and $PackQuantity!=''">
                <xsl:variable name="TotalQuantity" select='$Quantity * $PackQuantity'/>
                <ArtikelBestellung>
                    <fkKategorie>
                        <xsl:value-of select="$ItemCode"/>
                    </fkKategorie>
                    <Menge>
                        <xsl:value-of select="$TotalQuantity"/>
                    </Menge>
                </ArtikelBestellung>
            </xsl:if>

        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Requester -->
    <xsl:template name="Requester">

        <xsl:param name="Site"/>

        <xsl:if test="$Site">
            <Besteller>
                <!-- Name of the requesting facility -->
                <Name>
                    <xsl:value-of select="$Site/data[@field='name']/text()"/>
                </Name>
                <Zusatz></Zusatz> <!-- omit? -->

                <!-- Location details for the requesting facility -->
                <xsl:variable name="LocationUUID" select="$Site/reference[@field='location_id']/@uuid"/>
                <xsl:variable name="Location" select="//resource[@name='gis_location' and @uuid=$LocationUUID]"/>
                <xsl:if test="$Location">
                    <xsl:variable name="L4" select="$Location/data[@field='L4']/text()"/>
                    <xsl:variable name="L3" select="$Location/data[@field='L4']/text()"/>
                    <Straße>
                        <xsl:value-of select="$Location/data[@field='addr_street']/text()"/>
                    </Straße>
                    <PLZ>
                        <xsl:value-of select="$Location/data[@field='addr_postcode']/text()"/>
                    </PLZ>
                    <Ort>
                        <xsl:choose>
                            <xsl:when test="$L4!=''">
                                <xsl:value-of select="$L4"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$L3"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </Ort>
                </xsl:if>

                <!-- Contact Details for the requesting facility -->
                <Telefon>
                    <xsl:value-of select="$Site/data[@field='phone1']/text()"/>
                </Telefon>
                <Email>
                    <xsl:value-of select="$Site/data[@field='email']/text()"/>
                </Email>

                <!-- The requesting user -->
                <Ansprechpartner>
                    <xsl:variable name="RequesterUUID" select="reference[@field='requester_id']/@uuid"/>
                    <xsl:variable name="Requester" select="//resource[@name='pr_person' and @uuid=$RequesterUUID]"/>
                    <xsl:if test="$Requester">
                        <xsl:value-of select="concat($Requester/data[@field='first_name']/text(), ' ',
                                                     $Requester/data[@field='last_name']/text())"/>
                    </xsl:if>
                </Ansprechpartner>
            </Besteller>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hide everything else -->
    <xsl:template match="*"/>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
