<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Catalog Items - CSV Import Stylesheet

         CSV fields:
         Catalog.........................supply_catalog.name
         Category Code...................supply_item_category.code
         Category........................supply_item_category.name
         Item Code.......................supply_item.code

         Optional fields:
         Item Name.......................supply_item.name
         Brand...........................supply_item.brand
         Model...........................supply_item.model
         Year............................supply_item.year
         Unit of Measure.................supply_item.um             * Mandatory for New Items
         Unit Value......................supply_item.unit_value
         Currency........................supply_item.currency
         Pack............................supply_item_pack.name
         Pack Quantity...................supply_item_pack.quantity
         Pack2...........................supply_item_pack.name
         Pack2 Quantity..................supply_item_pack.quantity
         Pack3...........................supply_item_pack.name
         Pack3 Quantity..................supply_item_pack.quantity
         Weight..........................supply_item.weight
         Length..........................supply_item.length
         Width...........................supply_item.width
         Height..........................supply_item.height
         Volume..........................supply_item.volume
         Kit.............................supply_item.kit
         URL.............................supply_item.url
         Image...........................supply_item.file (URL to remote server to download)
         Distributed.....................supply_distribution_item (boolean to create)
         Comments........................supply_item.comments

         supply_catalog_item uses references to supply_catalog,
                                                supply_item_category,
                                                supply_item

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    
    <xsl:key name="catalog" match="row" use="col[@field='Catalog']"/>
    <xsl:key name="item_category" match="row" use="col[@field='Category']"/>
    <xsl:key name="supply_item" match="row" use="concat(col[@field='Item Name'],col[@field='Item Code'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>

            <!-- Catalogs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('catalog', col[@field='Catalog'])[1])]">
                <xsl:call-template name="Catalog"/>
            </xsl:for-each>

           <!-- Item Categories -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('item_category', col[@field='Category'])[1])]">
                <xsl:call-template name="ItemCategory"/>
            </xsl:for-each>

            <!-- Items -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('supply_item', concat(col[@field='Item Name'],col[@field='Item Code']))[1])]">
                <xsl:call-template name="SupplyItem"/>
            </xsl:for-each>

            <!-- Catalog Item -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="item" select="concat(col[@field='Item Name'],col[@field='Item Code'])"/>
        
        <!-- Supply Catalog Item -->
        <resource name="supply_catalog_item">
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$catalog"/>
                </xsl:attribute>
            </reference>
            <reference field="item_category_id" resource="supply_item_category">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$category"/>
                </xsl:attribute>
            </reference>
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Catalog">
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>

        <resource name="supply_catalog">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$catalog"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$catalog"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ItemCategory">
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>

        <resource name="supply_item_category">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$category"/>
            </xsl:attribute>
            <!-- Link to Supply Catalog -->
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$catalog"/>
                </xsl:attribute>
            </reference>
            <data field="code"><xsl:value-of select="col[@field='Category Code']"/></data>
            <data field="name"><xsl:value-of select="$category"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItem">
        <xsl:variable name="item_name" select="col[@field='Item Name']"/>
        <xsl:variable name="item_code" select="col[@field='Item Code']"/>
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="currency" select="col[@field='Currency']/text()"/>
        <xsl:variable name="um" select="col[@field='Unit of Measure']/text()"/>
        <xsl:variable name="pack" select="col[@field='Pack']"/>
        <xsl:variable name="UnitValue" select="col[@field='Unit Value']"/>
        <xsl:variable name="Brand" select="col[@field='Brand']"/>
        <xsl:variable name="Model" select="col[@field='Model']"/>
        <xsl:variable name="Year" select="col[@field='Year']"/>
        <xsl:variable name="Weight" select="col[@field='Weight']"/>
        <xsl:variable name="Length" select="col[@field='Length']"/>
        <xsl:variable name="Width" select="col[@field='Width']"/>
        <xsl:variable name="Height" select="col[@field='Height']"/>
        <xsl:variable name="Volume" select="col[@field='Volume']"/>
        <xsl:variable name="URL" select="col[@field='URL']"/>
        <xsl:variable name="Comments" select="col[@field='Comments']"/>
        <xsl:variable name="distributed">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Distributed']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="kit">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Kit']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($item_name, $item_code)"/>
            </xsl:attribute>
            <data field="code"><xsl:value-of select="$item_code"/></data>
            <xsl:if test="$item_name!=''">
                <data field="name"><xsl:value-of select="$item_name"/></data>
            </xsl:if>
            <xsl:if test="$um!=''">
                <data field="um"><xsl:value-of select="$um"/></data>
            </xsl:if>
            <xsl:if test="$UnitValue!=''">
                <data field="unit_value"><xsl:value-of select="$UnitValue"/></data>
            </xsl:if>
            <xsl:if test="$currency!=''">
                <data field="currency"><xsl:value-of select="$currency"/></data>
            </xsl:if>
            <xsl:if test="$Brand!=''">
                <data field="brand"><xsl:value-of select="$Brand"/></data>
            </xsl:if>
            <xsl:if test="$Model!=''">
                <data field="model"><xsl:value-of select="$Model"/></data>
            </xsl:if>
            <xsl:if test="$Year!=''">
                <data field="year"><xsl:value-of select="$Year"/></data>
            </xsl:if>
            <xsl:if test="$Weight!=''">
                <data field="weight"><xsl:value-of select="$Weight"/></data>
            </xsl:if>
            <xsl:if test="$Length!=''">
                <data field="length"><xsl:value-of select="$Length"/></data>
            </xsl:if>
            <xsl:if test="$Width!=''">
                <data field="width"><xsl:value-of select="$Width"/></data>
            </xsl:if>
            <xsl:if test="$Height!=''">
                <data field="height"><xsl:value-of select="$Height"/></data>
            </xsl:if>
            <xsl:if test="$Volume!=''">
                <data field="volume"><xsl:value-of select="$Volume"/></data>
            </xsl:if>
            <xsl:if test="$URL!=''">
                <data field="url"><xsl:value-of select="$URL"/></data>
            </xsl:if>
            <xsl:if test="$Comments!=''">
                <data field="comments"><xsl:value-of select="$Comments"/></data>
	        </xsl:if>
            <xsl:if test="$kit='Y' or $kit='YES' or $kit='T' or $kit='TRUE'">
	            <data field="kit" value="true">True</data>
	        </xsl:if>

            <!-- Image -->
            <xsl:if test="col[@field='Image']!=''">
                <data field="file">
                    <xsl:attribute name="url">
                        <xsl:value-of select="col[@field='Image']"/>
                    </xsl:attribute>
                </data>
            </xsl:if>

            <!-- Link to Supply Catalog -->
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$catalog"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Supply Item Category -->
            <reference field="item_category_id" resource="supply_item_category">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$category"/>
                </xsl:attribute>
            </reference>
            <!-- Supply Item Packs-->
	        <xsl:if test="$um!=''">
                <resource name="supply_item_pack">
                    <data field="name"><xsl:value-of select="$um"/></data>
                    <data field="quantity">1</data>
                </resource>
	        </xsl:if>
	        <xsl:if test="$pack!=''">
	            <resource name="supply_item_pack">
	                <data field="name"><xsl:value-of select="$pack"/></data>
	                <data field="quantity"><xsl:value-of select="col[@field='Pack Quantity']"/></data>
	            </resource>
	        </xsl:if>
            <xsl:if test="col[@field='Pack2']!=''">
	            <resource name="supply_item_pack">
	                <data field="name"><xsl:value-of select="col[@field='Pack2']"/></data>
	                <data field="quantity"><xsl:value-of select="col[@field='Pack2 Quantity']"/></data>
	            </resource>
	        </xsl:if>
            <xsl:if test="col[@field='Pack3']!=''">
	            <resource name="supply_item_pack">
	                <data field="name"><xsl:value-of select="col[@field='Pack3']"/></data>
	                <data field="quantity"><xsl:value-of select="col[@field='Pack3 Quantity']"/></data>
	            </resource>
	        </xsl:if>
            <!-- Supply Distribution Items -->
	        <xsl:if test="$distributed='Y' or $distributed='YES' or $distributed='T' or $distributed='TRUE'">
	            <resource name="supply_distribution_item">
	                <data field="name"><xsl:value-of select="$item_name"/></data>
	            </resource>
	        </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
