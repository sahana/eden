<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:s3="http://eden.sahanafoundation.org/wiki/S3">

    <xsl:output method="xml"/>

    <xsl:key name="sites" match="resource[@name='org_facility' or @name='inv_warehouse']" use="@uuid"/>
    <xsl:key name="items" match="resource[@name='supply_item']" use="@uuid"/>
    <xsl:key name="packs" match="resource[@name='supply_item_pack']" use="@uuid"/>
    <xsl:key name="requesters" match="resource[@name='pr_person']" use="@uuid"/>
    <xsl:key name="locations" match="resource[@name='gis_location']" use="@uuid"/>
    <xsl:key name="requests" match="resource[@name='req_req']" use="data[@field='req_ref']/text()"/>

    <s3:fields tables="inv_send" select="req_ref,site_id,to_site_id"/>
    <s3:fields tables="inv_track_item" select="item_id,item_pack_id,quantity,req_item_id"/>

    <s3:fields tables="req_req_item" select="req_id"/>
    <s3:fields tables="req_req" select="req_ref,date,comments,requester_id"/>

    <s3:fields tables="supply_item" select="code"/>
    <s3:fields tables="supply_item_pack" select="quantity"/>
    <s3:fields tables="pr_person" select="first_name,last_name"/>

    <s3:fields tables="org_facility" select="name,phone1,email,location_id"/>
    <s3:fields tables="inv_warehouse" select="name,code,location_id"/>
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
            <xsl:apply-templates select="resource[@name='inv_send']"/>
        </CoronaWWS>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Shipment -->
    <xsl:template match="resource[@name='inv_send']">

        <!-- Lookup the request -->
        <xsl:variable name="ReqRef" select="data[@field='req_ref']/text()"/>
        <xsl:variable name="Request" select='key("requests", $ReqRef)[1]'/>

        <!-- Lookup the Sending Site -->
        <xsl:variable name="FromSiteUUID" select="reference[@field='site_id']/@uuid"/>
        <xsl:variable name="FromSite" select='key("sites", $FromSiteUUID)[1]'/>

        <!-- Lookup the Receiving Site -->
        <xsl:variable name="ToSiteUUID" select="reference[@field='to_site_id']/@uuid"/>
        <xsl:variable name="ToSite" select='key("sites", $ToSiteUUID)[1]'/>

        <xsl:if test="$ToSite">
            <Bestellung>
                <!-- Requester Information -->
                <xsl:call-template name="Requester">
                    <xsl:with-param name="FromSite" select="$FromSite"/>
                    <xsl:with-param name="ToSite" select="$ToSite"/>
                    <xsl:with-param name="RequesterRef" select="$Request/reference[@field='requester_id']"/>
                </xsl:call-template>

                <!-- Request Reference -->
                <ReferenzNr>
                    <xsl:value-of select="$ReqRef"/>
                </ReferenzNr>

                <!-- Request date, using local format DD.MM.YYYY rather than ISO-Format -->
                <Bestelldatum>
                    <xsl:value-of select="substring-before($Request/data[@field='date']/text(), ' ')"/>
                </Bestelldatum>

                <!-- Request comments -->
                <Anmerkungen>
                    <xsl:value-of select="$Request/data[@field='comments']/text()"/>
                </Anmerkungen>

                <!-- This is repeated in the <Besteller> element -->
                <Email>
                    <xsl:value-of select="$ToSite/data[@field='email']/text()"/>
                </Email>

                <!-- The requested items -->
                <xsl:apply-templates select="resource[@name='inv_track_item']"/>

            </Bestellung>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Request Item -->
    <xsl:template match="resource[@name='inv_track_item']">
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

        <xsl:param name="FromSite"/>
        <xsl:param name="ToSite"/>
        <xsl:param name="RequesterRef"/>

        <xsl:if test="$ToSite">
            <Besteller>
                <!-- Name of the requesting facility -->
                <Name>
                    <xsl:value-of select="$ToSite/data[@field='name']/text()"/>
                </Name>

                <!-- Distribution Site Code -->
                <Gemeindeschluessel>
                    <xsl:value-of select="$FromSite/data[@field='code']/text()"/>
                </Gemeindeschluessel>

                <!-- Location details for the requesting facility -->
                <xsl:variable name="LocationUUID" select="$ToSite/reference[@field='location_id']/@uuid"/>
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
                    <xsl:value-of select="$ToSite/data[@field='phone1']/text()"/>
                </Telefon>
                <Email>
                    <xsl:value-of select="$ToSite/data[@field='email']/text()"/>
                </Email>

                <!-- The requesting user -->
                <Ansprechpartner>
                    <xsl:variable name="RequesterUUID" select="$RequesterRef/@uuid"/>
                    <xsl:variable name="Requester" select="key('requesters', $RequesterUUID)[1]"/>
                    <xsl:choose>
                        <xsl:when test="$Requester">
                            <xsl:value-of select="concat($Requester/data[@field='first_name']/text(), ' ',
                                                         $Requester/data[@field='last_name']/text())"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$RequesterRef/text()"/>
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
