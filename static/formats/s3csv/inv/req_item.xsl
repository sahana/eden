<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Request Items - CSV Import Stylesheet

         CSV fields:
         Request........................inv_req_item.req_id & inv_req.req_ref (lookup only)
         Item...........................inv_req_item.item_id & supply_item.name (lookup only)
         Pack...........................inv_req_item.pack & supply_item_pack
         Quantity.......................inv_req_item.quantity
         Currency.......................inv_req_item.currency
         Value..........................inv_req_item.pack_value
         Comments.......................inv_req_item.comments

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="request" match="row" use="col[@field='Request']"/>
    <xsl:key name="item" match="row" use="concat(col[@field='Item'],
                                                 col[@field='Pack'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Requests -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('request',
                                                                       col[@field='Request'])[1])]">
                <xsl:call-template name="Request" />
            </xsl:for-each>

            <!-- Items & Packs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('item',
                                                                       concat(col[@field='Item'],
                                                                              col[@field='Pack']))[1])]">
                <xsl:call-template name="Item" />
            </xsl:for-each>

            <!-- Req Items -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Item" select="col[@field='Item']"/>
        <xsl:variable name="Pack" select="col[@field='Pack']"/>

        <!-- Request Item -->
        <resource name="inv_req_item">
            <reference field="req_id" resource="inv_req">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Request:', col[@field='Request'])"/>
                </xsl:attribute>
            </reference>
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Item:', $Item, $Pack)"/>
                </xsl:attribute>
            </reference>
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('ItemPack:', $Item, $Pack)"/>
                </xsl:attribute>
            </reference>
            <data field="quantity"><xsl:value-of select="col[@field='Quantity']"/></data>
            <xsl:if test="col[@field='Currency']!=''">
                <data field="currency"><xsl:value-of select="col[@field='Currency']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Value']!=''">
                <data field="pack_value"><xsl:value-of select="col[@field='Value']"/></data>
            </xsl:if>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Request">

        <xsl:variable name="Request" select="col[@field='Request']"/>

        <resource name="inv_req">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Request:', $Request)"/>
            </xsl:attribute>
            <data field="req_ref"><xsl:value-of select="$Request"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Item">

        <xsl:variable name="Item" select="col[@field='Item']"/>
        <xsl:variable name="Pack" select="col[@field='Pack']"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Item:', $Item, $Pack)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Item"/></data>
            <data field="um"><xsl:value-of select="$Pack"/></data>
        </resource>

        <resource name="supply_item_pack">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('ItemPack:', $Item, $Pack)"/>
            </xsl:attribute>
            <!-- Link to item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Item:', $Item, $Pack)"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="$Pack"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
