<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         HELIOS - CSV Import Stylesheet

         2011-Jul-28 / Fran Boon <fran AT aidiq DOT com>

         - use for import to org/office/inv_item resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be inv/inv_item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:
           
           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath
           
           You can add a third argument &ignore_errors
         CSV fields:
         COUNTRY.................org_organisation.location_id
         CODE_SHARE..............inv_inv_item.item_id.item_category_id
         CODE_ORG................inv_inv_item.item_id.code
         ORGANISATION............org_organisation
         DESCRIPTION.............inv_inv_item.item_id.name
         UOM.....................inv_inv_item.item_id.um
         QUANTITY................inv_inv_item.quantity or inv_recv_item.quantity
         STATUS..................inv_item or inv_recv_item or proc_plan_item (Stock, On Order or Planned Procurement)
         DATE....................inv_inv_item.expiry_date or inv_recv_item.recv_id.eta
         CONTACTS................org_office.comments

    *********************************************************************** -->
    <xsl:include href="../xml/countries.xsl"/>

    <xsl:key name="organisations"
             match="table/row"
             use="col[@field='ORGANISATION']/text()"/>

    <xsl:key name="countries"
             match="table/row"
             use="col[@field='COUNTRY']/text()"/>

    <xsl:key name="offices"
             match="table/row"
             use="concat(col[@field='ORGANISATION']/text(), ' (',
                         col[@field='COUNTRY']/text(), ')')"/>

    <!-- Create/Lookup the Item Catalog -->
    <xsl:variable name="CatalogName">
        <xsl:text>Interagency Shared Items</xsl:text>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Root template -->
    <xsl:template match="/">
        <s3xml>

            <resource name="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CatalogName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$CatalogName"/></data>
            </resource>

            <xsl:call-template name="org_organisation"/>
            <xsl:call-template name="org_office"/>

            <xsl:apply-templates match="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Organisation template -->
    <xsl:template name="org_organisation">
        <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations', col[@field='ORGANISATION']/text())[1])]">
            <xsl:for-each select="key('organisations', col[@field='ORGANISATION']/text())">
                <xsl:if test="position() = 1">


                    <xsl:variable name="OrgName" select="col[@field='ORGANISATION']/text()"/>

                    <resource name="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OrgName"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$OrgName"/></data>
                        <!-- International NGO
                        <data field="type">3</data> -->
                    </resource>
                </xsl:if>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Office template -->
    <xsl:template name="org_office">
        <xsl:for-each select="//row[generate-id(.)=generate-id(key('offices', concat(col[@field='ORGANISATION']/text(), ' (',
                                                                                     col[@field='COUNTRY']/text(), ')'))[1])]">
            <xsl:for-each select="key('offices', concat(col[@field='ORGANISATION']/text(), ' (',
                                                        col[@field='COUNTRY']/text(), ')'))">
                <xsl:if test="position() = 1">

                    <!-- Office Name -->
                    <xsl:variable name="CountryCode" select="col[@field='COUNTRY']/text()"/>
                    
                    <xsl:variable name="CountryName">
                        <xsl:call-template name="iso2countryname">
                            <xsl:with-param name="country" select="$CountryCode"/>
                        </xsl:call-template>
                    </xsl:variable>

                    <xsl:variable name="OrgName" select="col[@field='ORGANISATION']/text()"/>

                    <xsl:variable name="OfficeName">
                        <xsl:value-of select="$OrgName"/>
                        <xsl:text> (</xsl:text>
                        <xsl:value-of select="$CountryName"/>
                        <xsl:text>)</xsl:text>
                    </xsl:variable>

                    <!-- Create the Office Location -->
                    <resource name="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="concat($OrgName, ' ', $CountryName)"/></data>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="concat('urn:iso:std:iso:3166:-1:code:', $CountryCode)"/>
                            </xsl:attribute>
                        </reference>
                    </resource>

                    <!-- Create the Office -->
                    <resource name="org_office">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$OfficeName"/></data>
                        <data field="L0"><xsl:value-of select="$CountryName"/></data>
                        <data field="comments"><xsl:value-of select="col[@field='CONTACTS']"/></data>
                        <!-- Link to Organisation -->
                        <reference field="organisation_id" resource="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$OrgName"/>
                            </xsl:attribute>
                        </reference>
                        <!-- Link to Location -->
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$OfficeName"/>
                            </xsl:attribute>
                        </reference>
                    </resource>

                </xsl:if>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Item template -->
    <xsl:template match="row">

        <!-- Office Name -->
        <xsl:variable name="CountryCode" select="col[@field='COUNTRY']/text()"/>

        <xsl:variable name="CountryName">
            <xsl:call-template name="iso2countryname">
                <xsl:with-param name="country" select="$CountryCode"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="OrgName" select="col[@field='ORGANISATION']/text()"/>

        <xsl:variable name="OfficeName">
            <xsl:value-of select="$OrgName"/>
            <xsl:text> (</xsl:text>
            <xsl:value-of select="$CountryName"/>
            <xsl:text>)</xsl:text>
        </xsl:variable>

        <!-- Create the Item Category -->
        <xsl:variable name="ItemCategory" select="col[@field='CODE_SHARE']/text()"/>
        <resource name="supply_item_category">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ItemCategory"/>
            </xsl:attribute>
            <data field="code"><xsl:value-of select="$ItemCategory"/></data>
            <data field="name"><xsl:value-of select="$ItemCategory"/></data>
            <!-- Link to Catalog -->
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CatalogName"/>
                </xsl:attribute>
            </reference>
        </resource>

        <!-- Create the Supply Item -->
        <xsl:variable name="ItemPack" select="col[@field='UOM']/text()"/>
        <xsl:variable name="ItemName" select="col[@field='CODE_ORG']/text()"/>
        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ItemName"/>
            </xsl:attribute>
            <data field="code"><xsl:value-of select="$ItemName"/></data>
            <data field="name"><xsl:value-of select="col[@field='DESCRIPTION']/text()"/></data>
            <data field="um"><xsl:value-of select="$ItemPack"/></data>
            <!-- Link to Category -->
            <reference field="item_category_id" resource="supply_item_category">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ItemCategory"/>
                </xsl:attribute>
            </reference>
            <!-- Add Item to Catalog -->
            <resource name="supply_catalog_item">
                <!-- Link to Catalog -->
                <reference field="catalog_id" resource="supply_catalog">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CatalogName"/>
                    </xsl:attribute>
                </reference>
                <!-- Link to Category -->
                <reference field="item_category_id" resource="supply_item_category">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ItemCategory"/>
                    </xsl:attribute>
                </reference>
                <!-- Link to Item
                <reference field="item_id" resource="supply_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ItemName"/>
                    </xsl:attribute>
                </reference> -->
                <!-- Must include a field (workaround) -->
                <data field="comments">_</data>
            </resource>
        </resource>

        <!-- Create the Item Pack -->
        <resource name="supply_item_pack">
            <xsl:attribute name="tuid">
                <!-- Same pack name can refer to multiple items - currently need 1 per item -->
                <xsl:value-of select="concat($ItemPack,$ItemName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ItemPack"/></data>
            <data field="quantity">1</data>
            <!-- Link to Item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ItemName"/>
                </xsl:attribute>
            </reference>
        </resource>

        <!-- Is the Item 'In Stock', 'On Order' or 'Planned'? -->
        <xsl:choose>
            <xsl:when test="col[@field='STATUS']='STOCK'">
                <!-- Add Item to Inventory -->
                <resource name="inv_inv_item">
                    <data field="quantity"><xsl:value-of select="col[@field='QUANTITY']"/></data>
                    <data field="expiry_date"><xsl:value-of select="col[@field='DATE']"/></data>
                    <!-- Link to Office -->
                    <reference field="site_id" resource="org_office">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Supply Item -->
                    <reference field="item_id" resource="supply_item">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ItemName"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Item Pack -->
                    <reference field="item_pack_id" resource="supply_item_pack">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ItemPack,$ItemName)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="col[@field='STATUS']='ORDERED'">
                <!-- Add Order -->
                <resource name="inv_recv">
                    <xsl:attribute name="tuid">
                        <!-- One order per Item per Date -->
                        <xsl:value-of select="concat($ItemName,col[@field='DATE'])"/>
                    </xsl:attribute>
                    <data field="eta"><xsl:value-of select="col[@field='DATE']"/></data>
                    <!-- IN_PROCESS -->
                    <data field="status"><xsl:text>0</xsl:text></data>
                    <!-- Link to Office -->
                    <reference field="site_id" resource="org_office">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                    </reference>
                </resource>
                <!-- Add Order Item -->
                <resource name="inv_recv_item">
                    <data field="quantity"><xsl:value-of select="col[@field='QUANTITY']"/></data>
                    <!-- Link to Supply Item -->
                    <reference field="item_id" resource="supply_item">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ItemName"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Item Pack -->
                    <reference field="item_pack_id" resource="supply_item_pack">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ItemPack,$ItemName)"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Order -->
                    <reference field="recv_id" resource="inv_recv">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ItemName,col[@field='DATE'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="col[@field='STATUS']='PLANNED'">
                <!-- Add Plan -->
                <resource name="proc_plan">
                    <xsl:attribute name="tuid">
                        <!-- One plan per Item per Date -->
                        <xsl:value-of select="concat($ItemName,col[@field='DATE'])"/>
                    </xsl:attribute>
                    <data field="eta"><xsl:value-of select="col[@field='DATE']"/></data>
                    <!-- Link to Office -->
                    <reference field="site_id" resource="org_office">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                    </reference>
                </resource>
                <!-- Add Plan Item -->
                <resource name="proc_plan_item">
                    <data field="quantity"><xsl:value-of select="col[@field='QUANTITY']"/></data>
                    <!-- Link to Supply Item -->
                    <reference field="item_id" resource="supply_item">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ItemName"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Item Pack -->
                    <reference field="item_pack_id" resource="supply_item_pack">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ItemPack,$ItemName)"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Plan -->
                    <reference field="plan_id" resource="proc_plan">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ItemName,col[@field='DATE'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:otherwise>
                <!-- Error! -->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
