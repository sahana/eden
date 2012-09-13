<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Inventory Send Item - CSV Import Stylesheet

         - use for import to /inv/send_item/create resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be inv/send_item/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors

         CSV fields:
         sender.................inv_sender_id,    *  part of the inv_send key
         recipient..............inv_recipient_id, *  part of the inv_send key
         date...................inv_send.date,    *  part of the inv_send key
         delivery_date..........inv_send.delivery_date
         warehouse..............inv_send.site_id -> inv_warehouse.name
         to_site_id.............inv_send.to_site_id
         status.................inv_send.status
         inv_send.comments......inv_send.comments
         Catalog................supply_catalog_item.catalog_id.name
         item...................inv_send_item.item_id -> supply_item.name
         item_pack..............inv_send_item.item_pack_id -> supply_item_pack.id & supply_item.um
         item_model.............supply_item.model
         quantity...............inv_send_item.quantity
         request_date...........inv_send_item.req_id -> req_req.date
         request_quantity.......inv_send_item.req_id -> req_req.quantity
         inv_send_item.comments.inv_send_item.comments

         The expectation is that the warehouse and site_id already exist, so it
         should just be a case of looking up their id. If they don't exist then
         they will be created but not all of the data (such as location) will
         be added to the record. The same is true for the people records, the
         item and pack records.

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="org_warehouse"
             match="row"
             use="col[@field='warehouse']"/>

    <xsl:key name="inv_warehouse"
             match="row"
             use="col[@field='to_site_id']"/>

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

<!-- ***********************************************************************
    At this stage we don't need to worry about the request record
    keep this code here just incase it is useful...

    <xsl:key name="req_req"
             match="row"
             use="concat(col[@field='recipient'], '/',
                         col[@field='request_date'])"/>

    <xsl:key name="req_item"
             match="row"
             use="concat(col[@field='recipient'], '/',
                         col[@field='request_date'], '/',
                         col[@field='inv_item'], '/',
                         col[@field='request_quantity'])"/>

    ************************************************************************ -->
    <xsl:key name="inv_send"
             match="row"
             use="concat(col[@field='sender'], '/',
                         col[@field='recipient'], '/',
                         col[@field='date'])"/>

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
            <!-- ******************************************************************
                 Search for each warehouse and create a unique warehouse record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('org_warehouse',
                                                        col[@field='warehouse'])[1])]">
                <xsl:call-template name="Place">
                    <xsl:with-param name="placename" select="col[@field='warehouse']"/>
                </xsl:call-template>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each destination and create a unique inv_warehouse record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('inv_warehouse',
                                                        col[@field='to_site_id'])[1])]">
                <xsl:call-template name="Place">
                    <xsl:with-param name="placename" select="col[@field='to_site_id']"/>
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
                 Search for each catalog and create a unique supply_catalog record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('catalog', col[@field='Catalog'])[1])]">
                <xsl:call-template name="Catalog"/>
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
                 Search for each inventory send and create a unique req_req record
                 ****************************************************************** -->

            <!-- *****************************************************************
                At this stage we don't need to worry about the request record
                keep this code here just incase it is useful...

            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('req_req',
                                                        concat(col[@field='recipient'], '/',
                                                               col[@field='request_date']))[1])]">
                <xsl:call-template name="Request"/>
            </xsl:for-each>
                 ****************************************************************** -->
            <!-- ******************************************************************
                 Search for each inventory send and create a unique inv_send record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('inv_send',
                                                        concat(col[@field='sender'], '/',
                                                               col[@field='recipient'], '/',
                                                               col[@field='date']))[1])]">
                <xsl:call-template name="Send"/>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each request item and create a unique req_item record
                 ****************************************************************** -->

            <!-- ******************************************************************
                At this stage we don't need to worry about the request record
                keep this code here just incase it is useful...

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
        <xsl:variable name="send_tuid" select="concat($sender, '/', $recipient, '/', $date)"/>
        <xsl:variable name="item" select="col[@field='item']/text()"/>
        <xsl:variable name="pack" select="col[@field='item_pack']/text()"/>
        <xsl:variable name="model" select="col[@field='item_model']/text()"/>
        <xsl:variable name="item_tuid" select="concat($item, '/', $pack, '/', $model)"/>
        <xsl:variable name="warehouse" select="col[@field='warehouse']/text()"/>
        <xsl:variable name="quantity" select="col[@field='quantity']/text()"/>
        <xsl:variable name="tuid" select="concat($send_tuid, '/', $item, '/', $pack)"/>
        <xsl:variable name="comments" select="col[@field='inv_send_item.comments']/text()"/>

        <resource name="inv_inv_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <!-- Link to warehouse -->
            <reference field="site_id" resource="inv_warehouse">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$warehouse"/>
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
        </resource>

        <resource name="inv_send_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <!-- Link to inv_send -->
            <reference field="send_id" resource="inv_send">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$send_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to inv_inv_item -->
            <reference field="inv_item_id" resource="inv_inv_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to supply_item_pack -->
            <reference field="item_pack_id" resource="supply_item_pack">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to req_item -->
            <!-- ******************************************************************
                At this stage we don't need to worry about the request record
                keep this code here just incase it is useful...

            <reference field="req_item_id" resource="req_req_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
                 ****************************************************************** -->

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
            <!-- Office Data -->
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

    <xsl:template name="Send">
        <xsl:variable name="sender" select="col[@field='sender']/text()"/>
        <xsl:variable name="recipient" select="col[@field='recipient']/text()"/>
        <xsl:variable name="date" select="col[@field='date']/text()"/>
        <xsl:variable name="delivery_date" select="col[@field='delivery_date']/text()"/>
        <xsl:variable name="tuid" select="concat($sender, '/', $recipient, '/', $date)"/>
        <xsl:variable name="warehouse" select="col[@field='warehouse']/text()"/>
        <xsl:variable name="destination" select="col[@field='to_site_id']/text()"/>
        <xsl:variable name="status" select="col[@field='status']/text()"/>
        <xsl:variable name="comments" select="col[@field='inv_send.comments']/text()"/>

        <!-- Create the inventory send record -->
        <resource name="inv_send">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <!-- Link to warehouse -->
            <reference field="site_id" resource="inv_warehouse">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$warehouse"/>
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
            <data field="delivery_date"><xsl:value-of select="$delivery_date"/></data>
            <data field="status"><xsl:value-of select="$status"/></data>
            <data field="comments"><xsl:value-of select="$comments"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

    <xsl:template name="Request">
        <xsl:variable name="requester" select="col[@field='recipient']/text()"/>
        <xsl:variable name="date" select="col[@field='request_date']/text()"/>
        <xsl:variable name="tuid" select="concat($requester, '/', $date)"/>
        <xsl:variable name="destination" select="col[@field='to_site_id']/text()"/>

        <!-- Create the req_req record -->
        <resource name="req_req">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <!-- Link to destination -->
            <reference field="to_site_id" resource="inv_warehouse">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$destination"/>
                </xsl:attribute>
            </reference>
            <!-- Link to requester (pr_person) -->
            <reference field="requester_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$requester"/>
                </xsl:attribute>
            </reference>
            <!-- inv_send Data -->
            <data field="date"><xsl:value-of select="$date"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

    <xsl:template name="RequestItem">
        <xsl:variable name="recipient" select="col[@field='recipient']/text()"/>
        <xsl:variable name="date" select="col[@field='request_date']/text()"/>
        <xsl:variable name="req_tuid" select="concat($recipient, '/', $date)"/>
        <xsl:variable name="item" select="col[@field='item']/text()"/>
        <xsl:variable name="pack" select="col[@field='item_pack']/text()"/>
        <xsl:variable name="model" select="col[@field='item_model']/text()"/>
        <xsl:variable name="item_tuid" select="concat($item, '/', $pack, '/', $model)"/>
        <xsl:variable name="quantity" select="col[@field='request_quantity']/text()"/>

        <!-- Create the req_req record -->
        <resource name="req_req_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item_tuid"/>
            </xsl:attribute>
            <!-- Link to request -->
            <reference field="req_id" resource="req_req">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$req_tuid"/>
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
            <!-- inv_send Data -->
            <data field="quantity"><xsl:value-of select="$quantity"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
