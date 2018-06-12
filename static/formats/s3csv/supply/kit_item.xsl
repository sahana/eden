<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Item Kits - CSV Import Stylesheet

         CSV fields:
         Kit.........................supply_kit_item.parent_item_id$name
         Item........................supply_kit_item.item_id$name
         Unit of Measure.............supply_kit_item.item_pack_id$name
         Quantity....................supply_kit_item.quantity

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    
    <xsl:key name="kit" match="row" use="col[@field='Kit']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Kits -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('kit', col[@field='Kit'])[1])]">
                <xsl:call-template name="Kit"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="item" select="col[@field='Item']/text()"/>
        <xsl:variable name="um" select="col[@field='Unit of Measure']/text()"/>

        <!-- Supply Item -->
        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$item"/></data>
            <data field="um"><xsl:value-of select="$um"/></data>
            <!-- Unit of Measure-->
	        <resource name="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($item, $um)"/>
                </xsl:attribute>
	            <data field="name"><xsl:value-of select="$um"/></data>
	            <data field="quantity">1</data>
	        </resource>
        </resource>

        <!-- Supply Kit Item -->
        <resource name="supply_kit_item">
            <reference field="parent_item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Kit']"/>
                </xsl:attribute>
            </reference>
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item"/>
                </xsl:attribute>
            </reference>
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($item, $um)"/>
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
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
