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
         Category Code..........supply_item_category.code
         Catalog................supply_catalog.name
         Brand..................supply_brand.name
         Item Code..............supply_item.code
         Item Name..............supply_item.name
         Unit of Measure........supply_item.um
         Model..................supply_item.model
         Year...................supply_item.year
         Weight.................supply_item.weight
         Length.................supply_item.length
         Width..................supply_item.width
         Height.................supply_item.height
         Volume.................supply_item.volume
         Tracking number........Tracking Number
         Comments...............comments
         Supplier/Donor.........supply_org_id
         Unit...................supply_item.um
         Currency...............currency
         Bin....................bin
         Unit Value.............pack_value
         Expiry Date............expiry_date
         Quantity...............inv_inv_item.quantity

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="catalog" match="row" use="col[@field='Catalog']"/>
    <xsl:key name="warehouse" match="row" use="col[@field='Warehouse']"/>
    <xsl:key name="item_category" match="row" use="col[@field='Category']"/>
    <xsl:key name="supply_item" match="row" use="concat(col[@field='Item Name'],col[@field='Item Code'])"/>
    <xsl:key name="brand" match="row" use="col[@field='Brand']"/>
    <xsl:key name="organisation" match="row" use="col[@field='Supplier/Donor']"/>

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

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Supplier/Donor'])[1])]">
                <xsl:call-template name="Organisation"/>
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
                <xsl:call-template name="SupplyItemPack"/>
            </xsl:for-each>

            <!-- Inventory Items -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="item" select="concat(col[@field='Item Name'],col[@field='Item Code'])"/>
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>

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
            <!-- Link to Supplier donor org -->
            <reference field="supply_org_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Supplier/Donor']/text()"/>
                </xsl:attribute>
            </reference>
            <data field="quantity"><xsl:value-of select="col[@field='Quantity']/text()"/></data>
            <data field="pack_value"><xsl:value-of select="col[@field='Unit Value']/text()"/></data>
            <data field="currency"><xsl:value-of select="col[@field='Currency']/text()"/></data>
            <data field="tracking_no"><xsl:value-of select="col[@field='Tracking number']/text()"/></data>
            <data field="bin"><xsl:value-of select="col[@field='Bin']/text()"/></data>
            <data field="expiry_date"><xsl:value-of select="col[@field='Expiry Date']/text()"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']/text()"/></data>
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
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" OrgName="select[@col='Supplier/Donor']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
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

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="col[@field='Item Name']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Item Code']"/></data>
            <data field="um"><xsl:value-of select="col[@field='Unit of Measure']"/></data>
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
        <xsl:variable name="item" select="concat(col[@field='Item Name'],col[@field='Item Code'])"/>

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
            <data field="name"><xsl:value-of select="col[@field='Unit of Measure']/text()"/></data>
            <data field="quantity">1</data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
