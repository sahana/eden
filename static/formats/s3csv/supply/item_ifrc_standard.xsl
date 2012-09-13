<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         IFRC Standard Catalog & Emergency Item Catalog (EIC) - CSV Import Stylesheet

         2011-06-20 / Michael Howden <michael AT aidiq DOT com>

         - use for import to supply/item resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be supply/item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         item code.......................
         item description................
         length cm.......................
         height cm.......................
         width cm........................
         volume litre....................
         weight kg.......................
         in EIC.......................... If "yes" add to catalog "EIC" too

        creates:
            supply_catalog...............
            supply_item_category.........
            supply_item..................
            supply_catalog_item..........

        @todo:

            - remove org_organisation (?)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:variable name="OrgName">International Federation of Red Cross and Red Crescent Societies</xsl:variable>
    <xsl:variable name="OrgAcronym">IFRC</xsl:variable>
    <xsl:variable name="IFRCStandard">IFRC Standard Catalog</xsl:variable>
    <xsl:variable name="EIC">EIC</xsl:variable>

    <xsl:key name="item" match="row" use="col[@field='item code']"/>
    <xsl:key name="category" match="row" use="substring(col[@field='item code']/text(),1,1)"/>
    <xsl:key name="subcategory" match="row" use="substring(col[@field='item code']/text(),1,4)"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgAcronym"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
                <data field="acronym"><xsl:value-of select="$OrgAcronym"/></data>
            </resource>

            <resource name="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$IFRCStandard"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$IFRCStandard"/></data>
            </resource>

            <resource name="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$EIC"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$EIC"/></data>

            </resource>

            <!-- Generate parent categories -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('category', substring(col[@field='item code']/text(),1,1))[1])]">
                <xsl:variable name="category_code" select="substring(col[@field='item code']/text(),1,1)"/>
                <!-- Add to IFRCStandard -->
                <xsl:call-template name="SupplyItemCategory">
                    <xsl:with-param name="id" select="$category_code"/>
                    <xsl:with-param name="category_code" select="$category_code"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Generate subcategories -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('subcategory', substring(col[@field='item code']/text(),1,3))[1])]">
                <xsl:variable name="id" select="substring(col[@field='item code']/text(),1,4)"/>
                <xsl:variable name="category_code" select="substring(col[@field='item code']/text(),2,4)"/>
                <xsl:variable name="parent_category_code" select="substring(col[@field='item code']/text(),1,1)"/>

                <!-- Add to IFRC Standard -->
                <xsl:call-template name="SupplyItemCategory">
                    <xsl:with-param name="id" select="$id"/>
                    <xsl:with-param name="category_code" select="$category_code"/>
                    <xsl:with-param name="parent_category_code" select="$parent_category_code"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Items -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Item -->
        <xsl:variable name="Category" select="substring(col[@field='item code']/text(),1,4)"/>
        <xsl:variable name="Code" select="col[@field='item code']/text()"/>
        <xsl:variable name="Name" select="col[@field='item description']/text()"/>
        <xsl:variable name="Length" select="col[@field='length cm']/text()"/>
        <xsl:variable name="Height" select="col[@field='height cm']/text()"/>
        <xsl:variable name="Width" select="col[@field='width cm']/text()"/>
        <xsl:variable name="Volume" select="col[@field='volume litre']/text()"/>
        <xsl:variable name="Weight" select="col[@field='weight kg']/text()"/>
        <xsl:variable name="InEIC" select="col[@field='in EIC']/text()"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Code"/>
            </xsl:attribute>

            <!-- Item Data -->
            <data field="code"><xsl:value-of select="$Code"/></data>
            <data field="name"><xsl:value-of select="$Name"/></data>
            <data field="length"><xsl:value-of select="$Length"/></data>
            <data field="height"><xsl:value-of select="$Height"/></data>
            <data field="width"><xsl:value-of select="$Width"/></data>
            <data field="volume"><xsl:value-of select="$Volume"/></data>
            <data field="weight"><xsl:value-of select="$Weight"/></data>
            <!-- Link to Supply Catalog -->
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$IFRCStandard"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Category -->
            <reference field="item_category_id" resource="supply_item_category">
                <xsl:attribute name="tuid">
                    <xsl:value-of select=" $Category"/>
                </xsl:attribute>
            </reference>

            <!-- Link to IFRC Standard-->
            <resource name="supply_catalog_item">
                <!-- Link to Catalog -->
                <reference field="catalog_id" resource="supply_catalog">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$IFRCStandard"/>
                    </xsl:attribute>
                </reference>
                <!-- Link to Category -->
                <reference field="item_category_id" resource="supply_item_category">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Category"/>
                    </xsl:attribute>
                </reference>
                <!-- Must include a field (workaround) -->
                <data field="comments">_</data>
            </resource>

            <!-- Link to EIC -->
            <xsl:if test="$InEIC = 'yes'">
                <resource name="supply_catalog_item">
                    <!-- Link to Catalog -->
                    <reference field="catalog_id" resource="supply_catalog">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$EIC"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Category -->
                    <reference field="item_category_id" resource="supply_item_category">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select=" $Category"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Must include a field (workaround) -->
                    <data field="comments">_</data>
                </resource>
            </xsl:if>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SupplyItemCategory">
        <xsl:param name="id"/>
        <xsl:param name="category_code"/>
        <xsl:param name="parent_category_code"/>

        <resource name="supply_item_category">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$id"/>
            </xsl:attribute>
            <reference field="catalog_id" resource="supply_catalog">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$IFRCStandard"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="$parent_category_code">
                <reference field="parent_item_category_id" resource="supply_item_category">
                    <xsl:attribute name="tuid">
                         <xsl:value-of select="$parent_category_code"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <data field="code"><xsl:value-of select="$category_code"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
