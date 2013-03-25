<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:param name="utcnow"/>

    <xsl:key name="stations" match="row" use="col[@field='Code']"/>
    <xsl:key name="supply_items" match="row" use="concat(col[@field='Type'], ', ',
                                                         col[@field='Model'], ', ',
                                                         col[@field='Brand'])"/>
    <xsl:key name="brands" match="row" use="normalize-space(col[@field='Brand'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Default Catalog -->
            <resource name="supply_catalog" tuid="default">
                <data field="name">Default</data>
            </resource>

            <!-- Vehicle Category -->
            <resource name="supply_item_category" tuid="vehicles">
                <data field="name">Vehicles</data>
                <data field="is_vehicle" value="true"/>
                <reference field="catalog_id" resource="supply_catalog" tuid="default"/>
            </resource>

            <!-- Fire Stations-->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('stations',
                                                        col[@field='Code'])[1])]">
                <xsl:call-template name="FireStation"/>
            </xsl:for-each>

            <!-- Brands -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('brands',
                                                        normalize-space(col[@field='Brand']))[1])]">
                <xsl:call-template name="Brand"/>
            </xsl:for-each>

            <!-- SupplyItems -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('supply_items',
                                                        concat(col[@field='Type'], ', ',
                                                               col[@field='Model'], ', ',
                                                               col[@field='Brand']))[1])]">
                <xsl:call-template name="SupplyItem"/>
            </xsl:for-each>

            <!-- Vehicles -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="StationCode" select="col[@field='Code']"/>
        <xsl:variable name="VehicleName" select="concat(col[@field='Type'], '-',
                                                        col[@field='Number'])"/>

        <xsl:call-template name="Vehicle"/>
        <xsl:call-template name="Asset"/>

        <resource name="fire_station_vehicle">
            <reference field="vehicle_id" resource="vehicle_vehicle">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$VehicleName"/>
                </xsl:attribute>
            </reference>
            <reference field="station_id" resource="fire_station">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$StationCode"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Vehicle">
        <xsl:variable name="VehicleName" select="concat(col[@field='Type'], '-',
                                                        col[@field='Number'])"/>

        <xsl:variable name="VehicleID" select="concat(col[@field='Code'], '-',
                                                      col[@field='Type'], '-',
                                                      col[@field='Number'])"/>

        <resource name="vehicle_vehicle">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$VehicleName"/>
            </xsl:attribute>
            <reference field="asset_id" resource="asset_asset">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$VehicleID"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Asset">
        <xsl:variable name="VehicleID" select="concat(col[@field='Code'], '-',
                                                      col[@field='Type'], '-',
                                                      col[@field='Number'])"/>

        <xsl:variable name="ItemCode" select="concat(col[@field='Type'], ', ',
                                                     col[@field='Model'], ', ',
                                                     col[@field='Brand'])"/>

        <xsl:variable name="StationCode" select="col[@field='Code']"/>

        <resource name="asset_asset">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$VehicleID"/>
            </xsl:attribute>
            <data field="type">1</data>
            <data field="purchase_date"><xsl:value-of select="concat(normalize-space(col[@field='Year']), '-01-01')"/></data>
            <resource name="asset_log">
                <data field="status" value="1"/>
                <data field="cond">1</data>
                <data field="datetime"><xsl:value-of select="$utcnow"/></data>
                <data field="site_or_location">1</data>
                <reference field="site_id" resource="fire_station">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$StationCode"/>
                    </xsl:attribute>
                </reference>
            </resource>
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ItemCode"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="FireStation">
        <xsl:variable name="StationCode" select="col[@field='Code']"/>

        <resource name="fire_station">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$StationCode"/>
            </xsl:attribute>
            <data field="code"><xsl:value-of select="$StationCode"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Brand">
        <xsl:variable name="BrandName" select="normalize-space(col[@field='Brand']/text())"/>

        <resource name="supply_brand">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$BrandName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$BrandName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItem">

        <xsl:variable name="ItemCode" select="concat(col[@field='Type'], ', ',
                                                     col[@field='Model'], ', ',
                                                     col[@field='Brand'])"/>

        <xsl:variable name="BrandName" select="normalize-space(col[@field='Brand'])"/>
        <xsl:variable name="Model" select="col[@field='Model']/text()"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ItemCode"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ItemCode"/></data>
            <xsl:if test="$BrandName!=''">
                <reference field="brand_id" resource="supply_brand">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$BrandName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <data field="model"><xsl:value-of select="$Model"/></data>
            <data field="um">piece</data>

            <resource name="supply_catalog_item">
                <reference field="catalog_id" resource="supply_catalog" tuid="default"/>
                <reference field="item_category_id" resource="supply_item_category" tuid="vehicles"/>
            </resource>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
