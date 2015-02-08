<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Item Categories - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be supply/catalog_item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Catalog.........................supply_catalog.name
         Category Code...................supply_item_category.code
         Category........................supply_item_category.name
         Item Code.......................supply_item.code
         Item Name.......................supply_item.name
         Brand...........................supply_brand.name
         Model...........................supply_item.model
         Year............................supply_item.year
         Unit of Measure.................supply_item.um
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
         Comments........................supply_item.comments

         supply_catalog_item uses references to supply_catalog,
                                                supply_item_category,
                                                supply_item

    *********************************************************************** -->
    <xsl:output method="xml"/>
    
    <xsl:key name="catalog" match="row" use="col[@field='Catalog']"/>
    <xsl:key name="item_category" match="row" use="col[@field='Category']"/>
    <xsl:key name="supply_item" match="row" use="concat(col[@field='Item Name'],col[@field='Item Code'])"/>
    <xsl:key name="brand" match="row" use="col[@field='Brand']"/>

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

            <!-- Brand -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('brand', col[@field='Brand'])[1])]">
                <xsl:call-template name="Brand"/>
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
    <xsl:template name="Brand">
        <resource name="supply_brand">
            <xsl:attribute name="tuid">
                <xsl:value-of select="col[@field='Brand']"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Brand']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ItemCategory">
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="category_code" select="col[@field='Category']/text()"/>
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
        <xsl:variable name="item" select="concat(col[@field='Item Name'],col[@field='Item Code'])"/>
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="um" select="col[@field='Unit of Measure']"/>
        <xsl:variable name="pack" select="col[@field='Pack']"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Item Name']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Item Code']"/></data>
            <data field="um"><xsl:value-of select="$um"/></data>
            <data field="model"><xsl:value-of select="col[@field='Model']"/></data>
            <data field="year"><xsl:value-of select="col[@field='Year']"/></data>
            <data field="weight"><xsl:value-of select="col[@field='Weight']"/></data>
            <data field="length"><xsl:value-of select="col[@field='Length']"/></data>
            <data field="width"><xsl:value-of select="col[@field='Width']"/></data>
            <data field="height"><xsl:value-of select="col[@field='Height']"/></data>
            <data field="volume"><xsl:value-of select="col[@field='Volume']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            <!-- Link to Brand -->
            <reference field="brand_id" resource="supply_brand">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Brand']"/>
                </xsl:attribute>
            </reference>
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
            <!-- Nest to Supply Item Pack-->
	        <resource name="supply_item_pack">
	            <data field="name"><xsl:value-of select="$um"/></data>
	            <data field="quantity">1</data>
	        </resource>
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
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
