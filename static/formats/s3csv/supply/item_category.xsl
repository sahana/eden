<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Item Categories - CSV Import Stylesheet

         CSV fields:
         Catalogue.......................supply_catalog.name
         Parent Category.................supply_item_category.parent_item_category_id$name
         Category........................supply_item_category.name
         Code............................supply_item_category.code
         Asset...........................supply_item_category.can_be_asset
         Telephone.......................supply_item_category.is_telephone
         Vehicle.........................supply_item_category.is_vehicle

    *********************************************************************** -->
    <xsl:output method="xml"/>
    
    <xsl:key name="catalog" match="row" use="col[@field='Catalogue']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
             <!-- Catalogues -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('catalog',
                                                        col[@field='Catalogue'])[1])]">
                <xsl:call-template name="Catalogue" />
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="CategoryName">
            <xsl:value-of select="col[@field='Category']"/>
        </xsl:variable>
        <xsl:variable name="Parent">
            <xsl:value-of select="col[@field='Parent Category']"/>
        </xsl:variable>

        <resource name="supply_item_category">

            <xsl:attribute name="tuid">
                <xsl:value-of select="$CategoryName"/>
            </xsl:attribute>

            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Catalogue']"/>
                </xsl:attribute>
            </reference>

            <data field="name"><xsl:value-of select="$CategoryName"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>

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

            <!-- Link to parent node (if any) -->
            <xsl:if test="$Parent!=''">
                <reference field="parent_item_category_id" resource="supply_item_category">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Parent"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

        </resource>
        
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Catalogues -->
    <xsl:template name="Catalogue">
        <xsl:variable name="CatalogName">
            <xsl:value-of select="col[@field='Catalogue']"/>
        </xsl:variable>

        <resource name="supply_catalog">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$CatalogName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CatalogName"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
