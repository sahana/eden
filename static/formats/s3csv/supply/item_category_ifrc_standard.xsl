<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Item Categories - CSV Import Stylesheet

         2011-06-20 / Michael Howden <michael AT aidiq DOT com>

         - use for import to supply/item_category resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be supply/item_category/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Organisation....................organisation.name
         Acronym.........................organisation.acronym
         Catalog.........................supply_catalog.name
         GROUP_CODE......................code
         GROUP_DESCRIPTION...............name
         FAM.............................code
         FAMILY_DESCRITPION..............name
         VEHICLE.........................is_vehicle

        creates:
            supply_catalog...............
            supply_item_category.........

        @todo:
            - remove org_organisation (?)

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- The Organisation (hardcoded here) -->
    <xsl:variable name="OrgName">International Federation of Red Cross and Red Crescent Societies</xsl:variable>
    <xsl:variable name="OrgAcronym">IFRC</xsl:variable>

    <!-- The Catalog (hardcoded here) -->
    <xsl:variable name="CatalogName">IFRC Standard Catalog</xsl:variable>

	<xsl:key name="catalogs" match="row" use="col[@field='Catalog']"/>
    <xsl:key name="groups" match="row" use="col[@field='GROUP_CODE']"/>

    <xsl:template match="/">
        <s3xml>
			<xsl:for-each select="//row[generate-id(.)=generate-id(key('catalogs', col[@field='Catalog'])[1])]">
			    <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
			    <xsl:variable name="OrgAcronym" select="col[@field='Acronym']/text()"/>
			    <xsl:variable name="CatalogName" select="col[@field='Catalog']/text()"/>

	            <resource name="org_organisation">
	                <xsl:attribute name="tuid">
	                    <xsl:value-of select="$OrgAcronym"/>
	                </xsl:attribute>
	                <data field="name"><xsl:value-of select="$OrgName"/></data>
	                <data field="acronym"><xsl:value-of select="$OrgAcronym"/></data>
	            </resource>

	            <resource name="supply_catalog">
	                <xsl:attribute name="tuid">
	                    <xsl:value-of select="$CatalogName"/>
	                </xsl:attribute>
	                <data field="name"><xsl:value-of select="$CatalogName"/></data>
	            </resource>
	            <xsl:for-each select="//row[generate-id(.)=generate-id(key('groups', col[@field='GROUP_CODE'])[1])]">
	                <!-- The Groups (Parent Item Categories) -->
	                <xsl:variable name="GroupCode" select="col[@field='GROUP_CODE']/text()"/>
	                <xsl:variable name="GroupName" select="col[@field='GROUP_DESCRIPTION']/text()"/>
	                <resource name="supply_item_category">
	                    <xsl:attribute name="tuid">
	                        <xsl:value-of select="$GroupCode"/>
	                    </xsl:attribute>
	                    <!-- Item Category Data -->
	                    <data field="code"><xsl:value-of select="$GroupCode"/></data>
	                    <data field="name"><xsl:value-of select="$GroupName"/></data>

	                    <!-- Link to Catalog -->
	                    <reference field="catalog_id" resource="supply_catalog">
	                        <xsl:attribute name="tuid">
	                            <xsl:value-of select="$CatalogName"/>
	                        </xsl:attribute>
	                    </reference>
		                <!-- Family Record (Item Categories) -->
		                <xsl:for-each select="key('groups', col[@field='GROUP_CODE'])">
			                <xsl:variable name="FamilyCode" select="col[@field='FAM']/text()"/>
			                <xsl:variable name="FamilyName" select="col[@field='FAMILY_DESCRITPION']/text()"/>
		                    <resource name="supply_item_category">
			                    <!--<xsl:attribute name="tuid">
			                        <xsl:value-of select="$FamilyCode"/>
			                    </xsl:attribute> -->
			                    <!-- Link to Catalog -->
			                    <reference field="catalog_id" resource="supply_catalog">
			                        <xsl:attribute name="tuid">
			                            <xsl:value-of select="$CatalogName"/>
			                        </xsl:attribute>
			                    </reference>

			                    <!-- Link to Group (parent)
		                        <reference field="parent_item_category_id" resource="supply_item_category">
		                            <xsl:attribute name="tuid">
		                                <xsl:value-of select="$GroupCode"/>
		                            </xsl:attribute>
		                        </reference> -->

		                        <!-- Item Category Data -->
			                    <data field="code"><xsl:value-of select="$FamilyCode"/></data>
			                    <data field="name"><xsl:value-of select="$FamilyName"/></data>
                                <xsl:if test="col[@field='VEHICLE']='Vehicle'">
                                    <data field="is_vehicle" value="true">True</data>
                                </xsl:if>
		                    </resource>
		                </xsl:for-each>
	                </resource>
                </xsl:for-each>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
