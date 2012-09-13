<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:inv="http://eden.sahanafoundation.inv/inv">

    <!-- **********************************************************************
         Inventory Warehouse - CSV Import Stylesheet

         1st May 2011 / Graeme Foster <graeme AT acm DOT org>

        CSV fields:
        Organisation..................track_org_id
        Tracking Number...............item_source_no
        Shipping Status...............status
        Warehouse.....................inv_inv_item.site_id, inv_send.site_id, inv_recv.from_site_id
        Catalog.......................supply_catalog_item.catalog_id.name
        Supply Item...................inv_inv_item.item_id, supply_item.name
        Bin...........................bin, inv_inv_item.bin
        Unit of Measure...............supply_item_pack
        Item Model....................supply_item.model
        Supplier/Donor................inv_inv_item.supply_org_id
        Currency......................currency
        Unit Value....................pack_value
        Expiry Date...................expiry_date
        Quantity Sent.................quantity
        Name of Sender................inv_send.sender_id, inv_recv.sender_id
        Date Sent.....................date
        Sent Status...................inv_send.status
        Destination Site..............inv_inv_item.site_id, inv_send.site_id, inv_recv.from_site_id
        Name of Recipient.............inv_send.recipient_id, inv_recv.recipient_id
        Estimated Date of Arrival.....inv_send.delivery_date, inv_recv.eta
        Date Received.................inv_recv.date
        Receiving Type................inv_recv.type
        Receiving Status..............inv_recv.status
        Quantity Received.............recv_quantity
        Receiving Bin.................recv_bin
        Comments......................comments
        Send Comments.................inv_send.comments
        Receiving Comments............inv_recv.comments
        Request Number................req_req.req_ref

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- shipping status, see modules/eden/inv.py -->
    <inv:shipstatus code="0">In Process</inv:shipstatus>
    <inv:shipstatus code="1">Received</inv:shipstatus>
    <inv:shipstatus code="2">Sent</inv:shipstatus>
    <inv:shipstatus code="3">Canceled</inv:shipstatus>

    <!-- tracking status, see modules/eden/inv.py -->
    <inv:trackstatus code="0">Unknown</inv:trackstatus>
    <inv:trackstatus code="1">Preparing</inv:trackstatus>
    <inv:trackstatus code="2">In transit</inv:trackstatus>
    <inv:trackstatus code="3">Unloading</inv:trackstatus>
    <inv:trackstatus code="4">Arrived</inv:trackstatus>
    <inv:trackstatus code="5">Canceled</inv:trackstatus>

    <!-- receiving type, see modules/eden/inv.py -->
    <inv:recvtype code="0">Other Warehouse</inv:recvtype>
    <inv:recvtype code="1">Donation</inv:recvtype>
    <inv:recvtype code="2">Supplier</inv:recvtype>

    <xsl:key name="organistion"
             match="row"
             use="col[@field='Organisation']"/>

    <xsl:key name="donor"
             match="row"
             use="col[@field='Supplier/Donor']"/>

    <xsl:key name="warehouse"
             match="row"
             use="col[@field='Warehouse']"/>

    <xsl:key name="site"
             match="row"
             use="col[@field='Destination Site']"/>

    <xsl:key name="pr_sender"
             match="row"
             use="col[@field='Name of Sender']"/>

    <xsl:key name="pr_recipient"
             match="row"
             use="col[@field='Name of Recipient']"/>

    <xsl:key name="catalog" match="row" use="col[@field='Catalog']"/>

    <xsl:key name="supply_item"
             match="row"
             use="concat(col[@field='Supply Item'], '/',
                         col[@field='Item Model'], '/',
                         col[@field='Unit of Measure'])"/>

    <xsl:key name="shipping"
             match="row"
             use="concat(col[@field='Name of Sender'],
                         col[@field='Name of Recipient'],
                         col[@field='Warehouse'],
                         col[@field='Destination Site'],
                         col[@field='Date Sent'])"/>

    <xsl:key name="request"
             match="row"
             use="col[@field='Request Number']"/>

    <xsl:key name="req_item"
             match="row"
             use="concat(col[@field='Request Number'], '/',
                         col[@field='Supply Item'], '/',
                         col[@field='Item Model'], '/',
                         col[@field='Unit of Measure'])"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>

            <!-- ******************************************************************
                 Search for each organisation (shipping org and supplier or donor org)
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('organistion',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName" select="col[@field='Organisation']"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('donor',
                                                        col[@field='Supplier/Donor'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName" select="col[@field='Supplier/Donor']"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- ******************************************************************
                 Search for each warehouse and create a unique warehouse record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('warehouse',
                                                        col[@field='Warehouse'])[1])]">
                <xsl:call-template name="Site">
                    <xsl:with-param name="placename" select="col[@field='Warehouse']"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('site',
                                                        col[@field='Destination Site'])[1])]">
                <xsl:call-template name="Site">
                    <xsl:with-param name="placename" select="col[@field='Destination Site']"/>
                </xsl:call-template>
            </xsl:for-each>
            
            <!-- ******************************************************************
                 Search for each person sending items
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('pr_sender',
                                                        col[@field='Name of Sender'])[1])]">
                <xsl:call-template name="Person">
                    <xsl:with-param name="name" select="col[@field='Name of Sender']"/>
                </xsl:call-template>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for each person receiving items
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('pr_recipient',
                                                        col[@field='Name of Recipient'])[1])]">

                <xsl:call-template name="Person">
                    <xsl:with-param name="name" select="col[@field='Name of Recipient']"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- ******************************************************************
                 Search for each catalog and create a unique supply_catalog record
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('catalog', col[@field='Catalog'])[1])]">
                <xsl:call-template name="Catalog"/>
            </xsl:for-each>

            <!-- ******************************************************************
                 Search for each supply item
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('supply_item',
                                                        concat(col[@field='Supply Item'], '/',
                                                        col[@field='Item Model'], '/',
                                                        col[@field='Unit of Measure']))[1])]">
                <xsl:call-template name="SupplyItem"/>
                <xsl:call-template name="SupplyItemPack"/>
            </xsl:for-each>

            <!-- ******************************************************************
                 Search for each shipping
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('shipping',
                                                        concat(col[@field='Name of Sender'],
                                                               col[@field='Name of Recipient'],
                                                               col[@field='Warehouse'],
                                                               col[@field='Destination Site'],
                                                               col[@field='Date Sent']
                                                              ))[1])]">
                <xsl:call-template name="Send"/>
                <xsl:call-template name="Recv"/>
            </xsl:for-each>

            <!-- ******************************************************************
                 Search for any responses to requests
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('request',
                                                        col[@field='Request Number'])[1])]">
                <xsl:call-template name="Request"/>
            </xsl:for-each>
            <!-- ******************************************************************
                 Search for any requests items
                 ****************************************************************** -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('req_item',
                                                        concat(
                                                               col[@field='Request Number'], '/',
                                                               col[@field='Supply Item'], '/',
                                                               col[@field='Item Model'], '/',
                                                               col[@field='Unit of Measure']
                                                              ))[1])]">
                <xsl:call-template name="Req_item"/>
            </xsl:for-each>


        </s3xml>
    </xsl:template>



    <!-- ******************************************************************
         Step through each row creating a inv_track_item record
         ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="orgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="donorName" select="col[@field='Supplier/Donor']/text()"/>
        <xsl:variable name="item" select="col[@field='Supply Item']/text()"/>
        <xsl:variable name="pack" select="col[@field='Unit of Measure']/text()"/>
        <xsl:variable name="model" select="col[@field='Item Model']/text()"/>
        <xsl:variable name="currency" select="col[@field='Currency']/text()"/>
        <xsl:variable name="unit_value" select="col[@field='Unit Value']/text()"/>
        <xsl:variable name="expiry_date" select="col[@field='Expiry Date']/text()"/>
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
        <xsl:variable name="destination" select="col[@field='Destination Site']/text()"/>
        <xsl:variable name="s_bin" select="col[@field='Bin']/text()"/>
        <xsl:variable name="r_bin" select="col[@field='Receiving Bin']/text()"/>

        <xsl:variable name="statusname" select="col[@field='Shipping Status']"/>
        <xsl:variable name="status" select="document('')//inv:trackstatus[text()=normalize-space($statusname)]/@code"/>
        <xsl:variable name="s_statusname" select="col[@field='Sent Status']"/>
        <xsl:variable name="s_status" select="document('')//inv:shipstatus[text()=normalize-space($s_statusname)]/@code"/>
        <xsl:variable name="r_statusname" select="col[@field='Receiving Status']"/>
        <xsl:variable name="r_status" select="document('')//inv:shipstatus[text()=normalize-space($r_statusname)]/@code"/>

        <xsl:variable name="sender" select="col[@field='Name of Sender']/text()"/>
        <xsl:variable name="recipient" select="col[@field='Name of Recipient']/text()"/>
        <xsl:variable name="date" select="col[@field='Date Sent']/text()"/>
        <xsl:variable name="eta" select="col[@field='Estimated Date of Arrival']/text()"/>
        <xsl:variable name="comments" select="col[@field='Comments']/text()"/>
        <xsl:variable name="tracking_no" select="col[@field='Tracking Number']/text()"/>
        <xsl:variable name="sent_quantity" select="col[@field='Quantity Sent']/text()"/>
        <xsl:variable name="recv_quantity" select="col[@field='Quantity Received']/text()"/>
        <xsl:variable name="reqNum" select="col[@field='Request Number']/text()"/>

        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $pack, '/', $model)"/>
        <xsl:variable name="pack_tuid" select="concat('supply_item_pack/',$item, '/', $pack, '/', $model)"/>
        <xsl:variable name="s_tuid" select="concat('inv_item/',$item, '/', $pack, '/', $model, '/', $warehouse, '/', $s_bin)"/>
        <xsl:variable name="r_tuid" select="concat('inv_item/',$item, '/', $pack, '/', $model, '/', $destination, '/', $r_bin)"/>

        <xsl:variable name="send_tuid" select="concat('inv_send/', $sender, '/', $recipient, '/', $warehouse, '/', $destination, '/', $date)"/>
        <xsl:variable name="recv_tuid" select="concat('inv_recv/', $sender, '/', $recipient, '/', $warehouse, '/', $destination, '/', $date)"/>
        <xsl:variable name="tuid" select="concat('track_item/', $item, '/', $warehouse, '/', $destination, '/', $date)"/>

        <!-- Find the inventory record that is sending the items -->
        <xsl:if test="$s_status">
            <xsl:call-template name="StockItem">
                <xsl:with-param name="site" select="col[@field='Warehouse']"/>
                <xsl:with-param name="bin" select="col[@field='Bin']"/>
            </xsl:call-template>
        </xsl:if>

        <!-- Find the inventory record that is receiving the items -->
        <xsl:if test="$r_status">
            <xsl:call-template name="StockItem">
                <xsl:with-param name="site" select="col[@field='Destination Site']"/>
                <xsl:with-param name="bin" select="col[@field='Receiving Bin']"/>
                <xsl:with-param name="recv">true</xsl:with-param>
            </xsl:call-template>
        </xsl:if>

        <resource name="inv_track_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <data field="item_source_no"><xsl:value-of select="$tracking_no"/></data>
            <data field="status"><xsl:value-of select="$status"/></data>
            <data field="quantity"><xsl:value-of select="$sent_quantity"/></data>
            <data field="recv_quantity"><xsl:value-of select="$recv_quantity"/></data>
            <data field="currency"><xsl:value-of select="$currency"/></data>
            <data field="pack_value"><xsl:value-of select="$unit_value"/></data>
            <data field="expiry_date"><xsl:value-of select="$expiry_date"/></data>
            <data field="bin"><xsl:value-of select="$s_bin"/></data>
            <data field="recv_bin"><xsl:value-of select="$r_bin"/></data>
            <data field="comments"><xsl:value-of select="$comments"/></data>

            <!-- Link to the shipping org -->
            <reference field="track_org_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('org_org/',$orgName)"/>
                </xsl:attribute>
            </reference>
            <!-- Link to the supply org -->
            <reference field="supply_org_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('org_org/',$donorName)"/>
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
                    <xsl:value-of select="$pack_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to inv_send -->
            <reference field="send_id" resource="inv_send">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$send_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to the sent inventory -->
            <reference field="send_inv_item_id" resource="inv_inv_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$s_tuid"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="$reqNum">
                <!-- Link to a request -->
                <reference field="req_item_id" resource="req_req_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('req_req_item/',$reqNum,'/',$item_tuid)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:if test="$r_status">
                <!-- Link to inv_recv -->
                <reference field="recv_id" resource="inv_recv">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$recv_tuid"/>
                    </xsl:attribute>
                </reference>
                <!-- Link to the received inventory -->
                <reference field="recv_inv_item_id" resource="inv_inv_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$r_tuid"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('org_org/',$OrgName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="Site">
        <xsl:param name="placename"/>

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
    <xsl:template name="SupplyItem">
        <xsl:variable name="catalog" select="col[@field='Catalog']/text()"/>
        <xsl:variable name="item" select="col[@field='Supply Item']/text()"/>
        <xsl:variable name="pack" select="col[@field='Unit of Measure']/text()"/>
        <xsl:variable name="model" select="col[@field='Item Model']/text()"/>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $pack, '/', $model)"/>

        <!-- Create the supply item record -->
        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item_tuid"/>
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
    <xsl:template name="SupplyItemPack">
        <xsl:variable name="item" select="col[@field='Supply Item']/text()"/>
        <xsl:variable name="pack" select="col[@field='Unit of Measure']/text()"/>
        <xsl:variable name="model" select="col[@field='Item Model']/text()"/>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $pack, '/', $model)"/>
        <xsl:variable name="pack_tuid" select="concat('supply_item_pack/',$item, '/', $pack, '/', $model)"/>

        <!-- Create the supply item pack record -->
        <resource name="supply_item_pack">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$pack_tuid"/>
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

        <xsl:variable name="sender" select="col[@field='Name of Sender']/text()"/>
        <!-- only create a inv_send record if we have a sender -->
        <xsl:if test="$sender!=''">
            <xsl:variable name="recipient" select="col[@field='Name of Recipient']/text()"/>
            <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
            <xsl:variable name="destination" select="col[@field='Destination Site']/text()"/>
            <xsl:variable name="date" select="col[@field='Date Sent']/text()"/>
            <xsl:variable name="tuid" select="concat('inv_send/', $sender, '/', $recipient, '/', $warehouse, '/', $destination, '/', $date)"/>
            <xsl:variable name="delivery_date" select="col[@field='Estimated Date of Arrival']/text()"/>
            <xsl:variable name="s_statusname" select="col[@field='Sent Status']"/>
            <xsl:variable name="s_status" select="document('')//inv:shipstatus[text()=normalize-space($s_statusname)]/@code"/>
            <xsl:variable name="comments" select="col[@field='Send Comments']/text()"/>

            <!-- Create the Send inventory record -->
            <resource name="inv_send">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
                <data field="date"><xsl:value-of select="$date"/></data>
                <data field="delivery_date"><xsl:value-of select="$delivery_date"/></data>
                <xsl:if test="$s_status!=''">
                    <data field="status"><xsl:value-of select="$s_status"/></data>
                </xsl:if>
                <data field="comments"><xsl:value-of select="$comments"/></data>
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
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Recv">
        <xsl:variable name="sender" select="col[@field='Name of Sender']/text()"/>
        <xsl:variable name="recipient" select="col[@field='Name of Recipient']/text()"/>
        <xsl:variable name="warehouse" select="col[@field='Warehouse']/text()"/>
        <xsl:variable name="destination" select="col[@field='Destination Site']/text()"/>
        <xsl:variable name="date" select="col[@field='Date Sent']/text()"/>
        <xsl:variable name="tuid" select="concat('inv_recv/', $sender, '/', $recipient, '/', $warehouse, '/', $destination, '/', $date)"/>
        <xsl:variable name="eta" select="col[@field='Estimated Date of Arrival']/text()"/>

        <xsl:variable name="r_typename" select="col[@field='Receiving Type']"/>
        <xsl:variable name="r_type" select="document('')//inv:recvtype[text()=normalize-space($r_typename)]/@code"/>
        <xsl:variable name="r_statusname" select="col[@field='Receiving Status']"/>
        <xsl:variable name="r_status" select="document('')//inv:shipstatus[text()=normalize-space($r_statusname)]/@code"/>
        <xsl:variable name="comments" select="col[@field='Receiving Comments']/text()"/>

        <xsl:if test="$r_status">
            <!-- Create the Receive inventory record -->
            <resource name="inv_recv">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
                <data field="date"><xsl:value-of select="$date"/></data>
                <data field="eta"><xsl:value-of select="$eta"/></data>
                <xsl:if test="$r_type">
                    <data field="type"><xsl:value-of select="$r_type"/></data>
                </xsl:if>
                <data field="status"><xsl:value-of select="$r_status"/></data>
                <data field="comments"><xsl:value-of select="$comments"/></data>
                <!-- Link to warehouse -->
                <reference field="from_site_id" resource="inv_warehouse">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$warehouse"/>
                    </xsl:attribute>
                </reference>
                <!-- Link to destination -->
                <reference field="site_id" resource="inv_warehouse">
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
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="StockItem">
        
        <xsl:param name="site"/>
        <xsl:param name="bin"/>
        <xsl:param name="recv"/>
        
        <xsl:variable name="item" select="col[@field='Supply Item']/text()"/>
        <xsl:variable name="pack" select="col[@field='Unit of Measure']/text()"/>
        <xsl:variable name="currency" select="col[@field='Currency']/text()"/>
        <xsl:variable name="unit_value" select="col[@field='Unit Value']/text()"/>
        <xsl:variable name="model" select="col[@field='Item Model']/text()"/>
        <xsl:variable name="ownerName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="donorName" select="col[@field='Supplier/Donor']/text()"/>
        <xsl:variable name="tracking_no" select="col[@field='Tracking Number']/text()"/>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $pack, '/', $model)"/>
        <xsl:variable name="pack_tuid" select="concat('supply_item_pack/',$item, '/', $pack, '/', $model)"/>
        <xsl:variable name="s_tuid" select="concat('inv_item/',$item, '/', $pack, '/', $model, '/', $site, '/', $bin)"/>

        <resource name="inv_inv_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$s_tuid"/>
            </xsl:attribute>
            <data field="bin"><xsl:value-of select="$bin"/></data>
            <data field="item_source_no"><xsl:value-of select="$tracking_no"/></data>
            <data field="currency"><xsl:value-of select="$currency"/></data>
            <data field="pack_value"><xsl:value-of select="$unit_value"/></data>
            <xsl:if test="$recv">
                <data field="quantity">0</data>
            </xsl:if>
            <!-- Uncomment for testing purposes
                 Can help with the error:
                 inv_inv_item.quantity may not be NULL
            <data field="quantity">0</data>
            -->
            <!-- Link to warehouse -->
            <reference field="site_id" resource="inv_warehouse">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$site"/>
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
                    <xsl:value-of select="$pack_tuid"/>
                </xsl:attribute>
            </reference>
            <!-- Link to the owning org -->
            <reference field="owner_org_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('org_org/',$ownerName)"/>
                </xsl:attribute>
            </reference>
            <!-- Link to the supply org -->
            <reference field="supply_org_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('org_org/',$donorName)"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Request">
        <xsl:variable name="reqNum" select="col[@field='Request Number']/text()"/>

        <resource name="req_req">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('req_req/',$reqNum)"/>
            </xsl:attribute>
            <data field="req_ref"><xsl:value-of select="$reqNum"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Req_item">
        <xsl:variable name="reqNum" select="col[@field='Request Number']/text()"/>
        <xsl:variable name="item" select="col[@field='Supply Item']/text()"/>
        <xsl:variable name="pack" select="col[@field='Unit of Measure']/text()"/>
        <xsl:variable name="model" select="col[@field='Item Model']/text()"/>
        <xsl:variable name="item_tuid" select="concat('supply_item/',$item, '/', $pack, '/', $model)"/>

        <resource name="req_req_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('req_req_item/',$reqNum,'/',$item_tuid)"/>
            </xsl:attribute>
            <reference field="req_id" resource="req_req">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('req_req/',$reqNum)"/>
                </xsl:attribute>
            </reference>
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$item_tuid"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>


    <!-- ****************************************************************** -->

</xsl:stylesheet>
