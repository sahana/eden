<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Inventory Items - CSV Import Stylesheet

         CSV fields:
         Warehouse..............org_site.name
         Facility Type..........optional.....Office, Facility, Hospital, Shelter, Warehouse (default)
         Organisation...........org_site.organisation_id
         Category...............supply_item_category
         Category Code..........supply_item_category.code
         Catalog................supply_catalog.name
         Item Code..............supply_item.code
         Item Name..............supply_item.name
         Brand..................supply_brand.name
         Model..................supply_item.model
         Year...................supply_item.year
         Units..................supply_item.um
         Pack...................supply_item_pack.name
         Pack Quantity .........supply_item_pack.quantity
         Weight.................supply_item.weight
         Length.................supply_item.length
         Width..................supply_item.width
         Height.................supply_item.height
         Volume.................supply_item.volume
         Quantity...............inv_inv_item.quantity
         Unit Value.............inv_inv_item.pack_value
         Bin....................inv_inv_item.bin
         Expiry Date............inv_inv_item.expiry_date
         Supplier/Donor.........inv_inv_item.supply_org_id
         Tracking Number........inv_inv_item.tracking_no
         Owned By (Organisation/Branch).inv_inv_item.organisation_id
         Currency...............currency
         Comments...............comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Organisation">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Organisation</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Expiry">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Expiry</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="TrackingNumber">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">TrackingNumber</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Units">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Units</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="catalog" match="row" use="col[@field='Catalog']"/>
    <xsl:key name="warehouse" match="row" use="col[@field='Warehouse']"/>
    <xsl:key name="organisation" match="row"
             use="col[contains(
                      document('../labels.xml')/labels/column[@name='Organisation']/match/text(),
                      concat('|', @field, '|'))]"/>
    <xsl:key name="item_category" match="row" use="col[@field='Category']"/>
    <xsl:key name="supply_item" match="row"
             use="concat(col[@field='Item Name'],col[@field='Item Code'])"/>
    <xsl:key name="brand" match="row" use="col[@field='Brand']"/>
    <xsl:key name="owner_organisation" match="row"
             use="col[@field='Owned By (Organisation/Branch)']"/>
    <xsl:key name="supplier_organisation" match="row"
             use="col[@field='Supplier/Donor']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>

            <!-- Catalogs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('catalog',
                                                                       col[@field='Catalog'])[1])]">
                <xsl:call-template name="Catalog"/>
            </xsl:for-each>

            <!-- Warehouses -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('warehouse',
                                                                       col[@field='Warehouse'])[1])]">
                <xsl:call-template name="Warehouse"/>
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation',
                                                                       col[contains(
                                                                           document('../labels.xml')/labels/column[@name='Organisation']/match/text(),
                                                                           concat('|', @field, '|'))])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName" select="col[@field='Organisation']"/>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('owner_organisation',
                                                                       col[@field='Owned By (Organisation/Branch)'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName" select="col[@field='Owned By (Organisation/Branch)']"/>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('supplier_organisation',
                                                                       col[@field='Supplier/Donor'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName" select="col[@field='Supplier/Donor']"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Item Categories -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('item_category',
                                                                       col[@field='Category'])[1])]">
                <xsl:call-template name="ItemCategory"/>
            </xsl:for-each>

            <!-- Brand -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('brand',
                                                                       col[@field='Brand'])[1])]">
                <xsl:call-template name="Brand"/>
            </xsl:for-each>

            <!-- Items -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('supply_item',
                                                                       concat(col[@field='Item Name'],
                                                                              col[@field='Item Code']))[1])]">
                <xsl:call-template name="SupplyItem"/>
                <xsl:call-template name="SupplyItemPack"/>
            </xsl:for-each>

            <!-- Inventory Items -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="item" select="concat(col[@field='Item Name'],
                                                 col[@field='Item Code'])"/>
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="um">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Units"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="expiry">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Expiry"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="tracking">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$TrackingNumber"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="model" select="col[@field='Model']/text()"/>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $um, '/', $model)"/>
        <xsl:variable name="um_tuid" select="concat('supply_item_pack/',$item, '/', $um, '/', $model)"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>inv_warehouse</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource name="inv_inv_item">
            <!-- Link to Supply Item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Supply Item Pack-->
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$um_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Warehouse -->
            <reference field="site_id">
                <xsl:attribute name="resource">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$warehouse"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Organisation -->
            <xsl:if test="col[@field='Owned By (Organisation/Branch)']!=''">
                <reference field="owner_org_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Owned By (Organisation/Branch)']"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <!-- Link to Supplier/Donor org -->
            <reference field="supply_org_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Supplier/Donor']"/>
                </xsl:attribute>
            </reference>
            <data field="quantity"><xsl:value-of select="col[@field='Quantity']"/></data>
            <xsl:if test="col[@field='Unit Value']!=''">
                <data field="pack_value"><xsl:value-of select="col[@field='Unit Value']"/></data>
                <xsl:if test="col[@field='Currency']!=''">
                    <data field="currency"><xsl:value-of select="col[@field='Currency']"/></data>
                </xsl:if>
            </xsl:if>
            <data field="tracking_no"><xsl:value-of select="$tracking"/></data>
            <data field="bin"><xsl:value-of select="col[@field='Bin']"/></data>
            <data field="expiry_date"><xsl:value-of select="$expiry"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>

        <xsl:if test="$OrgName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Catalog">
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="organisation">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Organisation"/>
            </xsl:call-template>
        </xsl:variable>

        <resource name="supply_catalog">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$catalog"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$catalog"/></data>
        </resource>
           <reference field="organisation_id" resource="org_organisation">
               <xsl:attribute name="tuid">
                   <xsl:value-of select="$organisation"/>
               </xsl:attribute>
           </reference>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Warehouse">
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="organisation">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Organisation"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>inv_warehouse</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource>
            <xsl:attribute name="name">
                <xsl:value-of select="$resourcename"/>
            </xsl:attribute>
            <xsl:attribute name="tuid">
                <xsl:value-of select="$warehouse"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$warehouse"/></data>
            <!-- Link to Warehouse Organisation org -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$organisation"/>
                </xsl:attribute>
            </reference>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Brand">
        <xsl:variable name="brand" select="col[@field='Brand']/text()"/>
        <resource name="supply_brand">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$brand"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$brand"/></data>
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
        <xsl:variable name="item" select="concat(col[@field='Item Name'],
                                                 col[@field='Item Code'])"/>
        <xsl:variable name="model" select="col[@field='Model']/text()"/>
        <xsl:variable name="category" select="col[@field='Category']/text()"/>
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="um">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Units"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="pack" select="col[@field='Pack']"/>
        <xsl:variable name="pack_quantity" select="col[@field='Pack Quantity']"/>
        <xsl:variable name="item_tuid" select="concat('supply_item/', $item, '/', $um, '/', $model)"/>
        <xsl:variable name="pack_tuid" select="concat('supply_item_pack/', $item, '/', $um, '/', $model)"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item_tuid"/>
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
            <!-- Nest to Supply Item Pack (UM)-->
            <resource name="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$pack_tuid"/>
                </xsl:attribute>
            </resource>
            <!-- Nest to Supply Item Pack-->
            <xsl:if test="$pack!=''">
                <resource name="supply_item_pack">
                    <data field="name"><xsl:value-of select="$pack"/></data>
                    <data field="quantity"><xsl:value-of select="$pack_quantity"/></data>
                </resource>
            </xsl:if>
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
        <xsl:variable name="item" select="concat(col[@field='Item Name'],
                                                 col[@field='Item Code'])"/>
        <xsl:variable name="um">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Units"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="model" select="col[@field='Model']/text()"/>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $um, '/', $model)"/>
        <xsl:variable name="um_tuid" select="concat('supply_item_pack/',$item, '/', $um, '/', $model)"/>

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
