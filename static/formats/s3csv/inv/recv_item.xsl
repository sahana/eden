<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Inventory Receive Item - CSV Import Stylesheet

         - use for import to /inv/recv_item/create resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be inv/recv_item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors

         CSV fields:
         destination............inv_recv.site_id -> inv_warehouse.name
         from_location..........inv_recv.from_site_id -> inv_warehouse.name
         recipient..............inv_recv.recipient_id
         sender.................inv_recv.sender_id
         eta....................inv_recv.eta
         date...................inv_recv.date
         type...................inv_recv.type
         status.................inv_recv.status
         organisation...........Not used
         inv_recv.comments......inv_recv.comments
         Catalog................supply_catalog_item.catalog_id.name
         item...................inv_recv_item.item_id -> supply_item.name
         item_pack..............inv_recv_item.item_id -> supply_item.name
         item_model.............inv_recv_item.item_id -> supply_item.model
         quantity...............inv_recv_item.quantity
         request................inv_recv_item.req_id -> req_req.request_number
         inv_recv_item.comments.inv_recv_item.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="org_destination"
             match="row"
             use="col[@field='destination']"/>

    <xsl:key name="org_source"
             match="row"
             use="col[@field='from_location']"/>

    <xsl:key name="pr_sender"
             match="row"
             use="col[@field='sender']"/>

    <xsl:key name="pr_recipient"
             match="row"
             use="col[@field='recipient']"/>

    <xsl:key name="catalog" match="row" use="col[@field='Catalog']"/>

    <xsl:key name="inv_item"
             match="row"
             use="concat(col[@field='item'], '/',
                         col[@field='item_model'], '/',
                         col[@field='item_pack'])"/>

    <xsl:key name="inv_item_pack"
             match="row"
             use="concat(col[@field='item'], '/',
                         col[@field='item_model'], '/',
                         col[@field='item_pack'])"/>

    <xsl:key name="inv_recv"
             match="row"
             use="concat(col[@field='sender'], '/',
                         col[@field='recipient'], '/',
                         col[@field='date'])"/>

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
            <!-- ******************************************************************
                 Search for each destination and create a unique inv_warehouse record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('org_destination',
                                                        col[@field='destination'])[1])]">
                <xsl:call-template name="Place">
                    <xsl:with-param name="placename" select="col[@field='destination']"/>
                </xsl:call-template>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each source and create a unique inv_warehouse record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('org_source',
                                                        col[@field='from_location'])[1])]">
                <xsl:call-template name="Place">
                    <xsl:with-param name="placename" select="col[@field='from_location']"/>
                </xsl:call-template>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each person sending items and create a unique pr_person record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('pr_sender',
                                                        col[@field='sender'])[1])]">
                <xsl:call-template name="Person">
                    <xsl:with-param name="name" select="col[@field='sender']"/>
                </xsl:call-template>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each person receiving items and create a unique pr_person record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('pr_recipient',
                                                        col[@field='recipient'])[1])]">

                <xsl:call-template name="Person">
                    <xsl:with-param name="name" select="col[@field='recipient']"/>
                </xsl:call-template>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each inventory item and create a unique inv_item record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('inv_item_pack',
                                                        concat(col[@field='item'], '/',
                                                               col[@field='item_model'], '/',
                                                               col[@field='item_pack']))[1])]">
                <xsl:call-template name="Item"/>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each catalog and create a unique supply_catalog record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('catalog', col[@field='Catalog'])[1])]">
                <xsl:call-template name="Catalog"/>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each inventory item and create a unique inv_item_pack record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('inv_item_pack',
                                                        concat(col[@field='item'], '/',
                                                               col[@field='item_model'], '/',
                                                               col[@field='item_pack']))[1])]">
                <xsl:call-template name="Item_Pack"/>
            </xsl:for-each>

            <!-- ******************************************************************
                 Search for each inventory received and create a unique inv_recv record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('inv_recv',
                                                        concat(col[@field='sender'], '/',
                                                               col[@field='recipient'], '/',
                                                               col[@field='date']))[1])]">
                <xsl:call-template name="Receive"/>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each request item and create a unique req_item record
                 ****************************************************************** -->

            <!-- ******************************************************************
                At this stage we don't need to worry about the request record
                keep this code her just incase it is useful...

            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('req_item',
                                                        concat(col[@field='recipient'], '/',
                                                               col[@field='request_date'], '/',
                                                               col[@field='inv_item'], '/',
                                                               col[@field='request_quantity']))[1])]">
                <xsl:call-template name="RequestItem"/>
            </xsl:for-each>
                 ****************************************************************** -->
        </s3xml>
    </xsl:template>

    <!-- ******************************************************************
         Step through each row creating an inventory sent item record
         ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="sender" select="col[@field='sender']/text()"/>
        <xsl:variable name="recipient" select="col[@field='recipient']/text()"/>
        <xsl:variable name="date" select="col[@field='date']/text()"/>
        <xsl:variable name="recv_tuid" select="concat($sender, '/', $recipient, '/', $date)"/>
        <xsl:variable name="item" select="col[@field='item']/text()"/>
        <xsl:variable name="pack" select="col[@field='item_pack']/text()"/>
        <xsl:variable name="model" select="col[@field='item_model']/text()"/>
        <xsl:variable name="item_tuid" select="concat($item, '/', $pack, '/', $model)"/>
        <xsl:variable name="quantity" select="col[@field='quantity']/text()"/>
        <xsl:variable name="tuid" select="concat($recv_tuid, '/', $item, '/', $pack)"/>
        <xsl:variable name="comments" select="col[@field='inv_recv_item.comments']/text()"/>


        <resource name="inv_recv_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <!-- Link to inv_send -->
            <reference field="recv_id" resource="inv_recv">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$recv_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to supply_item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to supply_item_pack -->
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
            <data field="quantity"><xsl:value-of select="$quantity"/></data>
            <data field="comments"><xsl:value-of select="$comments"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Place">
        <xsl:param name="placename"/>

        <!-- Create the place, an inv_warehouse record -->
        <resource name="inv_warehouse">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$placename"/>
            </xsl:attribute>
            <!-- Warehouse Data -->
            <data field="name"><xsl:value-of select="$placename"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">

        <xsl:param name="name"/>
        <xsl:variable name="firstName" select="substring-before($name,' ')"/>
        <xsl:variable name="lastName" select="substring-after($name,' ')"/>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$name"/>
            </xsl:attribute>
            <!-- Person record -->
            <data field="first_name"><xsl:value-of select="$firstName"/></data>
            <data field="last_name"><xsl:value-of select="$lastName"/></data>
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
    <xsl:template name="Item">
        <xsl:variable name="item" select="col[@field='item']/text()"/>
        <xsl:variable name="pack" select="col[@field='item_pack']/text()"/>
        <xsl:variable name="model" select="col[@field='item_model']/text()"/>
        <xsl:variable name="tuid" select="concat($item, '/', $pack, '/', $model)"/>

        <!-- Create the supply item record -->
        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <xsl:if test="$catalog!=''">
                <!-- Link to Supply Catalog -->
                <reference field="catalog_id" resource="supply_catalog">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$catalog"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <data field="name"><xsl:value-of select="$item"/></data>
            <data field="um"><xsl:value-of select="$pack"/></data>
            <data field="model"><xsl:value-of select="$model"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Item_Pack">
        <xsl:variable name="item" select="col[@field='item']/text()"/>
        <xsl:variable name="pack" select="col[@field='item_pack']/text()"/>
        <xsl:variable name="model" select="col[@field='item_model']/text()"/>
        <xsl:variable name="item_tuid" select="concat($item, '/', $pack, '/', $model)"/>

        <!-- Create the supply item pack record -->
        <resource name="supply_item_pack">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item_tuid"/>
            </xsl:attribute>
            <!-- Link to item -->
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="$pack"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Receive">
        <xsl:variable name="destination" select="col[@field='destination']/text()"/>
        <xsl:variable name="from_location" select="col[@field='from_location']/text()"/>
        <xsl:variable name="sender" select="col[@field='sender']/text()"/>
        <xsl:variable name="recipient" select="col[@field='recipient']/text()"/>
        <xsl:variable name="date" select="col[@field='date']/text()"/>
        <xsl:variable name="tuid" select="concat($sender, '/', $recipient, '/', $date)"/>
        <xsl:variable name="status" select="col[@field='status']/text()"/>
        <xsl:variable name="eta" select="col[@field='eta']/text()"/>
        <xsl:variable name="type" select="col[@field='type']/text()"/>
        <xsl:variable name="comments" select="col[@field='inv_recv.comments']/text()"/>

        <!-- Create the inventory send record -->
        <resource name="inv_recv">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <!-- Link to from_location -->
            <reference field="site_id" resource="inv_warehouse">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$from_location"/>
                </xsl:attribute>
            </reference>
            <!-- Link to destination -->
            <reference field="to_site_id" resource="inv_warehouse">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$destination"/>
                </xsl:attribute>
            </reference>
            <!-- Link to sender (pr_person) -->
            <reference field="sender_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$sender"/>
                </xsl:attribute>
            </reference>
            <!-- Link to recipient (pr_person) -->
            <reference field="recipient_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$recipient"/>
                </xsl:attribute>
            </reference>
            <!-- inv_send Data -->
            <data field="date"><xsl:value-of select="$date"/></data>
            <data field="status"><xsl:value-of select="$status"/></data>
            <data field="eta"><xsl:value-of select="$eta"/></data>
            <data field="type"><xsl:value-of select="$type"/></data>
            <data field="comments"><xsl:value-of select="$comments"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
