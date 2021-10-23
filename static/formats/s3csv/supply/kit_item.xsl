<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Item Kits - CSV Import Stylesheet

         CSV fields:
         Kit.........................supply_kit_item.parent_item_id$name
         Item Code...................supply_kit_item.item_id$code
         Item Name...................supply_kit_item.item_id$name
         Units.......................supply_kit_item.item_pack_id$name
         Quantity....................supply_kit_item.quantity

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Units">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Units</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    
    <xsl:key name="kit" match="row" use="col[@field='Kit']"/>
    <xsl:key name="supply_item" match="row"
             use="concat(col[@field='Item Name'],col[@field='Item Code'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Kits -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('kit', col[@field='Kit'])[1])]">
                <xsl:call-template name="Kit"/>
            </xsl:for-each>

            <!-- Items -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('supply_item',
                                                                       concat(col[@field='Item Name'],
                                                                              col[@field='Item Code']))[1])]">
                <xsl:call-template name="SupplyItem"/>
                <xsl:call-template name="SupplyItemPack"/>
            </xsl:for-each>


            <!-- Kit Items -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="item" select="concat(col[@field='Item Name'],
                                                 col[@field='Item Code'])"/>
        <xsl:variable name="um">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Units"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $um)"/>
        <xsl:variable name="pack_tuid" select="concat('supply_item_pack/', $item, '/', $um)"/>

        <resource name="supply_kit_item">
            <!-- Link to Kit -->
            <reference field="parent_item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Kit']/text()"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Kit Item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Item Pack -->
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$pack_tuid"/>
                </xsl:attribute>
            </reference>
            <data field="quantity"><xsl:value-of select="col[@field='Quantity']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Kit">
        <xsl:variable name="kit" select="col[@field='Kit']/text()"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$kit"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$kit"/></data>
            <data field="kit" value="true">True</data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItem">
        <xsl:variable name="ItemCode" select="col[@field='Item Code']/text()"/>
        <xsl:variable name="ItemName" select="col[@field='Item Name']/text()"/>
        <xsl:variable name="item" select="concat($ItemName, $ItemCode)"/>
        <xsl:variable name="um">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Units"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="item_tuid" select="concat('supply_item/', $item, '/', $um)"/>
        <xsl:variable name="pack_tuid" select="concat('supply_item_pack/', $item, '/', $um)"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item_tuid"/>
            </xsl:attribute>
            <xsl:if test="$ItemCode!=''">
                <data field="code"><xsl:value-of select="$ItemCode"/></data>
            </xsl:if>
            <xsl:if test="$ItemName!=''">
                <data field="name"><xsl:value-of select="$ItemName"/></data>
            </xsl:if>
            <!-- Nest to Supply Item Pack (UM)-->
            <resource name="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$pack_tuid"/>
                </xsl:attribute>
            </resource>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItemPack">
        <xsl:variable name="item" select="concat(col[@field='Item Name'],
                                                 col[@field='Item Code'])"/>
        <xsl:variable name="um">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Units"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $um)"/>
        <xsl:variable name="um_tuid" select="concat('supply_item_pack/',$item, '/', $um)"/>

        <!-- Create the supply item pack record -->
        <resource name="supply_item_pack">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$um_tuid"/>
            </xsl:attribute>
            <!-- Link to item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="$um"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
