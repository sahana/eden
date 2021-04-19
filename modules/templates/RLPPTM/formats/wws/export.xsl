<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:s3="http://eden.sahanafoundation.org/wiki/S3">

    <xsl:output method="xml"/>

    <xsl:key name="sites" match="resource[@name='org_facility' or @name='inv_warehouse']" use="@uuid"/>
    <xsl:key name="items" match="resource[@name='supply_item']" use="@uuid"/>
    <xsl:key name="packs" match="resource[@name='supply_item_pack']" use="@uuid"/>
    <xsl:key name="requesters" match="resource[@name='pr_person']" use="@uuid"/>
    <xsl:key name="locations" match="resource[@name='gis_location']" use="@uuid"/>

    <s3:fields tables="req_req" select="req_ref,date,site_id,comments,requester_id"/>
    <s3:fields tables="req_req_item" select="item_id,item_pack_id,quantity"/>

    <s3:fields tables="supply_item" select="code"/>
    <s3:fields tables="supply_item_pack" select="quantity"/>
    <s3:fields tables="pr_person" select="first_name,last_name"/>

    <s3:fields tables="org_facility" select="name,phone1,email,location_id"/>
    <s3:fields tables="inv_warehouse" select="name,location_id"/>
    <s3:fields tables="gis_location" select="L3,L4,addr_street,addr_postcode"/>

    <s3:fields tables="ANY" select="*"/>

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
        <xsl:variable name="Site" select='key("sites", $SiteUUID)[1]'/>

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

            <xsl:variable name="ItemCode" select="key('items', $ItemUUID)[1]/data[@field='code']/text()"/>
            <xsl:variable name="PackQuantity" select="key('packs', $PackUUID)[1]/data[@field='quantity']/@value"/>

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
                <xsl:variable name="Location" select="key('locations', $LocationUUID)[1]"/>
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
                    <xsl:variable name="Requester" select="key('requesters', $RequesterUUID)[1]"/>
                    <xsl:choose>
                        <xsl:when test="$Requester">
                            <xsl:value-of select="concat($Requester/data[@field='first_name']/text(), ' ',
                                                         $Requester/data[@field='last_name']/text())"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="reference[@field='requester_id']/text()"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </Ansprechpartner>
            </Besteller>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hide everything else -->
    <xsl:template match="*"/>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
