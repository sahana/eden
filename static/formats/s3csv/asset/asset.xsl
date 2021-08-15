<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Assets - CSV Import Stylesheet

         CSV fields:
         Organisation....................organisation_id.name & asset_log.organisation_id.name
         Team............................group.group_id.name
         Acronym.........................organisation_id.acronym & asset_log.organisation_id.acronym
         Facility........................site_id & asset_log.site_id
         Facility Code...................site_id.code & asset_log.site_id.code
         Facility Type......optional.....Facility, Hospital, Shelter, Warehouse, Office (default)
         Room............................asset_log.room_id
         Assigned To.....................pr_person.email <- @ToDo: Get this working
         Condition.......................asset_log.cond
         Catalog.........................supply_catalog_item.catalog_id.name
         Asset No........................number
         Type............................type
         Category........................supply_catalog_item.item_category_id
         Item Code.......................supply_item.code (useful to ensure explicit matching to existing Catalog items)
         Item Name.......................supply_item.name (alternative to code useful for adding new items on-the-fly)
         Brand...........................supply_brand.name
         Model...........................supply_item.model
         SN..............................sn
         Supplier........................supplier
         Purchase Date...................purchase_date
         Price...........................purchase_price
         Comments........................comments

        creates:
            supply_brand.................
            org_office...................
            org_organisation.............
            gis_location.................
            supply_catalog...............
            supply_item_category.........
            supply_item..................
            supply_catalog_item..........
            pr_person....................
            org_room.....................

        @todo:
            - remove id column
            - make in-line references explicit

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="organisations" match="row" use="col[@field='Organisation']/text()"/>
    <xsl:key name="groups" match="row" use="col[@field='Team']/text()"/>
    <xsl:key name="sites" match="row" use="concat(col[@field='Organisation']/text(), '|',
                                                  col[@field='Facility']/text(), '|',
                                                  col[@field='Facility Code']/text(), '|',
                                                  col[@field='Facility Type']/text())"/>
    <xsl:key name="rooms" match="row" use="concat(col[@field='Organisation']/text(), '|',
                                                  col[@field='Facility']/text(), '|',
                                                  col[@field='Facility Code']/text(), '|',
                                                  col[@field='Facility Type']/text(), '|',
                                                  col[@field='Room']/text())"/>
    <xsl:key name="persons" match="row" use="col[@field='Assigned To']/text()"/>
    <xsl:key name="brands" match="row" use="col[@field='Brand']/text()"/>
    <xsl:key name="catalogs" match="row" use="col[@field='Catalog']/text()"/>
    <xsl:key name="categories" match="row" use="concat(col[@field='Catalog']/text(), '|',
                                                       col[@field='Category']/text())"/>
    <xsl:key name="supply_items" match="row" use="concat(col[@field='Item Code'], ', ',
                                                         col[@field='Item Name'], ', ',
                                                         col[@field='Model'], ', ',
                                                         col[@field='Brand'])"/>
    <xsl:key name="supplier_organisation" match="row" use="col[@field='Supplier/Donor']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('organisations',
                                                        col[@field='Organisation']/text())[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName" select="col[@field='Organisation']/text()"/>
                    <xsl:with-param name="OrgAcronym" select="col[@field='Acronym']/text()"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Teams -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('groups',
                                                        col[@field='Team']/text())[1])]">
                <xsl:call-template name="Team"/>
            </xsl:for-each>

            <!-- Sites -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('sites',
                                                        concat(col[@field='Organisation']/text(), '|',
                                                               col[@field='Facility']/text(), '|',
                                                               col[@field='Facility Code']/text(), '|',
                                                               col[@field='Facility Type']/text()))[1])]">
                <xsl:call-template name="Site"/>
            </xsl:for-each>

            <!-- Rooms -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('rooms',
                                                        concat(col[@field='Organisation']/text(), '|',
                                                               col[@field='Facility']/text(), '|',
                                                               col[@field='Facility Code']/text(), '|',
                                                               col[@field='Facility Type']/text(), '|',
                                                               col[@field='Room']/text()))[1])]">
                <xsl:call-template name="Room"/>
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('persons',
                                                        col[@field='Assigned To']/text())[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Brands -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('brands',
                                                        col[@field='Brand']/text())[1])]">
                <xsl:call-template name="Brand"/>
            </xsl:for-each>

            <!-- SupplyCatalogs -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('catalogs',
                                                        col[@field='Catalog']/text())[1])]">
                <xsl:call-template name="SupplyCatalog"/>
            </xsl:for-each>

            <!-- SupplyItemCategories -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('categories',
                                                        concat(col[@field='Catalog']/text(), '|',
                                                               col[@field='Category']/text()))[1])]">
                <xsl:call-template name="SupplyItemCategory"/>
            </xsl:for-each>

            <!-- SupplyItems -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('supply_items',
                                                        concat(col[@field='Item Code'], ', ',
                                                               col[@field='Item Name'], ', ',
                                                               col[@field='Model'], ', ',
                                                               col[@field='Brand']))[1])]">
                <xsl:call-template name="SupplyItem"/>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('supplier_organisation', col[@field='Supplier/Donor'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName" select="col[@field='Supplier/Donor']"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="TeamName" select="col[@field='Team']/text()"/>
        <xsl:variable name="FacilityName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="FacilityCode" select="col[@field='Facility Code']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="FacilityTUID" select="concat($OrgName, '|', $FacilityName, '|', $FacilityCode, '|', $FacilityType)"/>
        <xsl:variable name="ItemTUID" select="concat(col[@field='Item Code'], ', ',
                                                     col[@field='Item Name'], ', ',
                                                     col[@field='Model'], ', ',
                                                     col[@field='Brand'])"/>

        <xsl:variable name="AssetNumber" select="col[@field='Asset No']/text()"/>
        <xsl:variable name="PurchaseDate" select="col[@field='Purchase Date']/text()"/>
        <xsl:variable name="Type" select="col[@field='Type']/text()"/>

        <xsl:variable name="AssignedTo" select="col[@field='Assigned To']/text()"/>
        <xsl:variable name="Condition" select="col[@field='Condition']/text()"/>
        <xsl:variable name="RoomName" select="col[@field='Room']/text()"/>
        <xsl:variable name="RoomTUID" select="concat($FacilityTUID, '|', $RoomName)"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Asset  -->
        <resource name="asset_asset">
            <xsl:if test="$AssetNumber != ''">
                <data field="number"><xsl:value-of select="$AssetNumber"/></data>
            </xsl:if>
            <xsl:if test="col[@field='SN'] != ''">
                <data field="sn"><xsl:value-of select="col[@field='SN']"/></data>
            </xsl:if>
            <xsl:if test="$Type != ''">
                <xsl:choose>
                    <xsl:when test="$Type=1">
                        <data field="type">1</data>
                    </xsl:when>
                    <xsl:when test="$Type='VEHICLE'">
                        <data field="type">1</data>
                    </xsl:when>
                    <xsl:when test="$Type='Vehicle'">
                        <data field="type">1</data>
                    </xsl:when>
                    <xsl:when test="$Type='vehicle'">
                        <data field="type">1</data>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
            <!-- Link to Supplier/Donor org -->
            <reference field="supply_org_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Supplier/Donor']/text()"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="$PurchaseDate!=''">
                <data field="purchase_date"><xsl:value-of select="$PurchaseDate"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Price'] != ''">
                <data field="purchase_price"><xsl:value-of select="col[@field='Price']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments'] != ''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ItemTUID"/>
                </xsl:attribute>
            </reference>
            <!-- Org -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgName"/>
                </xsl:attribute>
            </reference>
            <!-- Team -->
            <xsl:if test="$TeamName!=''">
                <resource name="asset_group">
                    <reference field="group_id" name="pr_group">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$TeamName"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
            <!-- Site -->
            <reference field="site_id">
                <xsl:attribute name="resource">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$FacilityTUID"/>
                </xsl:attribute>
            </reference>
            <!-- Log -->
            <resource name="asset_log">
                <data field="cond">
                    <xsl:choose>
                        <xsl:when test="$Condition=2">2</xsl:when>
                        <xsl:when test="$Condition='MINOR'">2</xsl:when>
                        <xsl:when test="$Condition='Minor'">2</xsl:when>
                        <xsl:when test="$Condition='minor'">2</xsl:when>
                        <xsl:when test="$Condition='MINOR DAMAGE'">2</xsl:when>
                        <xsl:when test="$Condition='Minor Damage'">2</xsl:when>
                        <xsl:when test="$Condition='minor damage'">2</xsl:when>
                        <xsl:when test="$Condition=3">3</xsl:when>
                        <xsl:when test="$Condition='MAJOR'">3</xsl:when>
                        <xsl:when test="$Condition='Major'">3</xsl:when>
                        <xsl:when test="$Condition='major'">3</xsl:when>
                        <xsl:when test="$Condition='MAJOR DAMAGE'">3</xsl:when>
                        <xsl:when test="$Condition='Major Damage'">3</xsl:when>
                        <xsl:when test="$Condition='major damage'">3</xsl:when>
                        <xsl:when test="$Condition=4">4</xsl:when>
                        <xsl:when test="$Condition='UN-REPAIRABLE'">4</xsl:when>
                        <xsl:when test="$Condition='Un-Repairable'">4</xsl:when>
                        <xsl:when test="$Condition='un-repairable'">4</xsl:when>
                        <xsl:when test="$Condition=5">5</xsl:when>
                        <xsl:when test="$Condition='NEEDS MAINTENANCE'">5</xsl:when>
                        <xsl:when test="$Condition='Needs Maintenance'">5</xsl:when>
                        <xsl:when test="$Condition='needs maintenance'">5</xsl:when>
                        <!-- Default to 'Good' -->
                        <xsl:otherwise>1</xsl:otherwise>
                    </xsl:choose>
                </data>
                <!-- Org -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
                <!-- Site -->
                <reference field="site_id">
                    <xsl:attribute name="resource">
                        <xsl:value-of select="$resourcename"/>
                    </xsl:attribute>
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$FacilityTUID"/>
                    </xsl:attribute>
                </reference>
                <!-- Room -->
                <xsl:if test="$RoomName!=''">
                    <reference field="room_id" resource="org_room">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$RoomTUID"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="$AssignedTo!=''">
                        <!-- Person -->
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$AssignedTo"/>
                            </xsl:attribute>
                        </reference>
                        <!-- 'Assigned' -->
                        <data field="status">2</data>
                        <data field="check_in_to_person">1</data>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Default to 'Base Facility Set' -->
                        <data field="status">1</data>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>
        <xsl:param name="OrgAcronym"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
            <xsl:if test="$OrgAcronym!=''">
                <data field="acronym"><xsl:value-of select="$OrgAcronym"/></data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Team">

        <xsl:variable name="TeamName" select="col[@field='Team']/text()"/>

        <xsl:if test="$TeamName!=''">
            <resource name="pr_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$TeamName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$TeamName"/></data>
                <data field="group_type"><xsl:text>3</xsl:text></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Site">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="FacilityName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="FacilityCode" select="col[@field='Facility Code']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="FacilityTUID" select="concat($OrgName, '|', $FacilityName, '|', $FacilityCode, '|', $FacilityType)"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource>
            <xsl:attribute name="name">
                <xsl:value-of select="$resourcename"/>
            </xsl:attribute>
            <xsl:attribute name="tuid">
                <xsl:value-of select="$FacilityTUID"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$FacilityName"/></data>
            <xsl:if test="col[@field='FacilityCode'] != ''">
                <data field="code"><xsl:value-of select="col[@field='FacilityCode']"/></data>
            </xsl:if>
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgName"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Room">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="FacilityName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="FacilityCode" select="col[@field='Facility Code']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="FacilityTUID" select="concat($OrgName, '|', $FacilityName, '|', $FacilityCode, '|', $FacilityType)"/>
        <xsl:variable name="RoomName" select="col[@field='Room']/text()"/>
        <xsl:variable name="RoomTUID" select="concat($FacilityTUID, '|', $RoomName)"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$RoomName!=''">
            <resource name="org_room">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$RoomTUID"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$RoomName"/></data>
                <reference field="site_id">
                    <xsl:attribute name="resource">
                        <xsl:value-of select="$resourcename"/>
                    </xsl:attribute>
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$FacilityTUID"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="AssignedTo" select="col[@field='Assigned To']/text()"/>

        <xsl:if test="$AssignedTo!=''">
            <resource name="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$AssignedTo"/>
                </xsl:attribute>
                <data field="first_name"><xsl:value-of select="$AssignedTo"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyCatalog">
        <xsl:variable name="CatalogName" select="col[@field='Catalog']/text()"/>

        <resource name="supply_catalog">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$CatalogName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CatalogName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItemCategory">
        <xsl:variable name="CatalogName" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="CategoryName" select="col[@field='Category']/text()"/>
        <xsl:variable name="CategoryTUID" select="concat($CatalogName, '|', $CategoryName)"/>

        <xsl:if test="$CategoryName!=''">
            <resource name="supply_item_category">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CategoryTUID"/>
                </xsl:attribute>
                <data field="code"><xsl:value-of select="substring($CategoryName,1,16)"/></data>
                <data field="name"><xsl:value-of select="$CategoryName"/></data>
                <reference field="catalog_id" resource="supply_catalog">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CatalogName"/>
                    </xsl:attribute>
                </reference>
                <data field="can_be_asset" value="true">True</data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItem">

        <xsl:variable name="CatalogName" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="CategoryName" select="col[@field='Category']/text()"/>
        <xsl:variable name="CategoryTUID" select="concat($CatalogName, '|', $CategoryName)"/>
        <xsl:variable name="BrandName" select="col[@field='Brand']/text()"/>
        <xsl:variable name="ItemCode" select="col[@field='Item Code']/text()"/>
        <xsl:variable name="ItemName" select="col[@field='Item Name']/text()"/>
        <xsl:variable name="Model" select="col[@field='Model']/text()"/>
        <xsl:variable name="ItemTUID" select="concat($ItemCode, ', ',
                                                     $ItemName, ', ',
                                                     $Model, ', ',
                                                     $BrandName)"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ItemTUID"/>
            </xsl:attribute>
            <xsl:if test="$ItemCode!=''">
                <data field="code"><xsl:value-of select="$ItemCode"/></data>
            </xsl:if>
            <xsl:if test="$ItemName!=''">
                <data field="name"><xsl:value-of select="$ItemName"/></data>
            </xsl:if>
            <xsl:if test="$Model!=''">
                <data field="model"><xsl:value-of select="$Model"/></data>
            </xsl:if>
            <data field="um">piece</data>
            <!-- Link to Supply Catalog -->
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CatalogName"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="$BrandName!=''">
                <reference field="brand_id" resource="supply_brand">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$BrandName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$CategoryName!=''">
                <!-- Link to Supply Item Category -->
                <reference field="item_category_id" resource="supply_item_category">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CategoryTUID"/>
                    </xsl:attribute>
                </reference>
                <!-- Nest to Supply Catalog -->
                <resource name="supply_catalog_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ItemTUID"/>
                    </xsl:attribute>
                    <!-- Link to Supply Catalog -->
                    <reference field="catalog_id" resource="supply_catalog">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$CatalogName"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Supply Item Category -->
                    <reference field="item_category_id" resource="supply_item_category">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$CategoryTUID"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Brand">
        <xsl:variable name="BrandName" select="col[@field='Brand']/text()"/>

        <resource name="supply_brand">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$BrandName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$BrandName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
