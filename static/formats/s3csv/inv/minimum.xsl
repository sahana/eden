<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Minimum Stock Levels - CSV Import Stylesheet

         CSV fields:
         Warehouse..............org_site.name
         Facility Type..........optional.....Office, Facility, Hospital, Shelter, Warehouse (default)
         Organisation...........org_site.organisation_id
         Item Code..............supply_item.code
         Item Name..............supply_item.name
         Units..................supply_item.um
         Quantity...............inv_minimum.quantity
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

    <xsl:variable name="Units">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Units</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="warehouse" match="row" use="col[@field='Warehouse']"/>
    <xsl:key name="organisation" match="row"
             use="col[contains(
                      document('../labels.xml')/labels/column[@name='Organisation']/match/text(),
                      concat('|', @field, '|'))]"/>
    <xsl:key name="supply_item" match="row"
             use="concat(col[@field='Item Name'],col[@field='Item Code'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>

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

            <!-- Items -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('supply_item',
                                                                       concat(col[@field='Item Name'],
                                                                              col[@field='Item Code']))[1])]">
                <xsl:call-template name="SupplyItem"/>
                <xsl:call-template name="SupplyItemPack"/>
            </xsl:for-each>

            <!-- Minimum Stock Levels -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="item" select="concat(col[@field='Item Name'],
                                                 col[@field='Item Code'])"/>
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="um">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Units"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $um)"/>

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

        <resource name="inv_minimum">
            <!-- Link to Supply Item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
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
            <data field="quantity"><xsl:value-of select="col[@field='Quantity']"/></data>
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
            <xsl:if test="$organisation!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$organisation"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
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
        <xsl:variable name="comments" select="col[@field='Comments']/text()"/>

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
            <data field="um"><xsl:value-of select="$um"/></data>
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
