<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Inventory Warehouse - CSV Import Stylesheet

         1st May 2011 / Graeme Foster <graeme AT acm DOT org>

         - use for import to /inv/warehouse/create resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be inv/warehouse/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors

         CSV fields:
         Warehouse..............org_office
         Category...............supply_item_category
         Item description.......supply_item.name
         Catalog         .......supply_catalog.name
         Tracking number (CTN)..
         Remark.................
         Outbound...............
         UM.....................supply_item.um
         Currency...............currency
         Price..................
         UM Value...............pack_value
         Stock..................
         Price..................
         Stock..................inv_inv_item.quantity
         Price..................
         Stock..................

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="catalog" match="row" use="col[@field='Catalog']"/>
    <xsl:key name="warehouse" match="row" use="col[@field='Warehouse']"/>
    <xsl:key name="item_category" match="row" use="col[@field='Category']"/>
    <xsl:key name="supply_item" match="row" use="col[@field='Item description']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>

            <!-- Catalogs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('catalog', col[@field='Catalog'])[1])]">
                <xsl:call-template name="Catalog"/>
            </xsl:for-each>

            <!-- Warehouses -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('warehouse', col[@field='Warehouse'])[1])]">
                <xsl:call-template name="Warehouse"/>
            </xsl:for-each>

            <!-- Item Categories -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('item_category', col[@field='Category'])[1])]">
                <xsl:call-template name="ItemCategory"/>
            </xsl:for-each>

            <!-- Items -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('supply_item', col[@field='Item description'])[1])]">
                <xsl:call-template name="SupplyItem"/>
                <xsl:call-template name="SupplyItemPack"/>
            </xsl:for-each>

            <!-- Inventory Items -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="item" select="col[@field='Item description']/text()"/>
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>

        <resource name="inv_inv_item">
            <!-- Link to Supply Item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Supply Item Pack-->
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Warehouse -->
            <reference field="site_id" resource="org_office">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$warehouse"/>
                </xsl:attribute>
            </reference>
            <data field="quantity"><xsl:value-of select="col[@field='Stock']/text()"/></data>
            <data field="pack_value"><xsl:value-of select="col[@field='UM Value']/text()"/></data>
            <data field="currency"><xsl:value-of select="col[@field='Currency']/text()"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Remark']/text()"/></data>
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
    <xsl:template name="Warehouse">
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>

        <resource name="org_office">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$warehouse"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$warehouse"/></data>
            <data field="type">5</data>
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
            <data field="code"><xsl:value-of select="substring($category/text(),1,16)"/></data>
            <data field="name"><xsl:value-of select="$category"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItem">
        <xsl:variable name="item" select="col[@field='Item description']/text()"/>
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$item"/></data>
            <data field="um"><xsl:value-of select="col[@field='UM']/text()"/></data>
            <!-- Link to Supply Item Category -->
            <reference field="item_category_id" resource="supply_item_category">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$category"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Supply Item Pack-->
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item"/>
                </xsl:attribute>
            </reference>
            <!-- Nest to Supply Catalog -->
	        <resource name="supply_catalog_item">
	            <xsl:attribute name="tuid">
	                <xsl:value-of select="$item"/>
	            </xsl:attribute>
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
	        </resource>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItemPack">
        <xsl:variable name="item" select="col[@field='Item description']/text()"/>

        <resource name="supply_item_pack">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item"/>
            </xsl:attribute>
            <!-- Link to Supply Item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="col[@field='UM']/text()"/></data>
            <data field="quantity">1</data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
