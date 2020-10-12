<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Subscription Plan - CSV Import Stylesheet
         
         CSV column...........Format..........Content

         Name.................string..........Name
         Description..........string..........Description
         Product..............string..........Product Name
         Months...............string..........Interval Count
         Price................string..........Price
         Currency.............string..........Currency

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="product" match="row" use="col[@field='Product']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Products -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('product',
                                                                       col[@field='Product'])[1])]">
                <xsl:call-template name="Product"/>
            </xsl:for-each>

            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="fin_subscription_plan">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="interval_count"><xsl:value-of select="col[@field='Months']"/></data>
            <data field="price"><xsl:value-of select="col[@field='Price']"/></data>
            <data field="currency"><xsl:value-of select="col[@field='Currency']"/></data>

            <!-- Link to Product -->
            <reference field="product_id" resource="fin_product">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Product']"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Product">
        <xsl:variable name="product" select="col[@field='Product']/text()"/>

        <resource name="fin_product">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$product"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$product"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
