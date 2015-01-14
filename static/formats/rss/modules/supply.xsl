<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- Supply -->
    
    <!-- supply_item_entity -->
    <!-- @ToDo: Add Virtual Fields -->
    <xsl:template match="resource[@name='supply_item_entity']" mode="contents">
        <xsl:variable name="Quantity" select="./data[@field='quantity']/text()"/>
        <xsl:variable name="UoM" select="./reference[@field='item_pack_id']/text()"/>
        <xsl:variable name="InstanceType" select="./data[@field='instance_type']/text()"/>
        <title>
            <xsl:value-of select="./reference[@field='item_id']/text()"/>
        </title>
        <description>
            <xsl:text>Quantity: </xsl:text>
            <xsl:value-of select="concat($Quantity, ' ',$UoM)"/>
            &lt;br/&gt;&lt;br/&gt;
            <xsl:text>Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="contains($InstanceType, 'Inventory')">
                    <xsl:text>Stock</xsl:text>
                </xsl:when>
                <xsl:when test="contains($InstanceType, 'Order')">
                    <xsl:text>On Order</xsl:text>
                </xsl:when>
                <xsl:when test="contains($InstanceType, 'Planned')">
                    <xsl:text>Planned Procurement</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </description>
    </xsl:template>

</xsl:stylesheet>
