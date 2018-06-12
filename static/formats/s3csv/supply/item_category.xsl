<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Item Categories - CSV Import Stylesheet

         CSV fields:
         Catalogue.......................supply_catalog.name
         Category........................supply_item_category.name
         Code............................supply_item_category.code
         Asset...........................supply_item_category.can_be_asset
         Telephone.......................supply_item_category.is_telephone
         Vehicle.........................supply_item_category.is_vehicle

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Supply Catalogue -->
        <xsl:variable name="CatalogName"><xsl:value-of select="col[@field='Catalogue']"/></xsl:variable>
        <resource name="supply_catalog">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$CatalogName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CatalogName"/></data>
        </resource>

        <!-- Supply Item Category -->
        <resource name="supply_item_category">
            <xsl:attribute name="tuid">
                <xsl:value-of select="col[@field='Category']"/>
            </xsl:attribute>
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CatalogName"/>
                </xsl:attribute>
            </reference>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="name"><xsl:value-of select="col[@field='Category']"/></data>
            <xsl:choose>
                <xsl:when test="col[@field='Asset']='Asset'">
                    <data field="can_be_asset" value="true">True</data>
                </xsl:when>
                <xsl:when test="col[@field='Asset']='True'">
                    <data field="can_be_asset" value="true">True</data>
                </xsl:when>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="col[@field='Telephone']='Telephone'">
                    <data field="is_telephone" value="true">True</data>
                </xsl:when>
                <xsl:when test="col[@field='Telephone']='True'">
                    <data field="is_telephone" value="true">True</data>
                </xsl:when>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="col[@field='Vehicle']='Vehicle'">
                    <data field="is_vehicle" value="true">True</data>
                </xsl:when>
                <xsl:when test="col[@field='Vehicle']='True'">
                    <data field="is_vehicle" value="true">True</data>
                </xsl:when>
            </xsl:choose>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
