<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Pallets - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Pallet Name
         Width................float...........Width (m)
         Length...............float...........Length (m)
         Depth................float...........Depth (m)
         Weight...............float...........Weight (kg)
         Load Capacity........float...........Load Capacity (kg)
         Max Height...........float...........Max Height (m)
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="inv_pallet">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="width"><xsl:value-of select="col[@field='Width']"/></data>
            <data field="length"><xsl:value-of select="col[@field='Length']"/></data>
            <data field="depth"><xsl:value-of select="col[@field='Depth']"/></data>
            <data field="weight"><xsl:value-of select="col[@field='Weight']"/></data>
            <data field="load_capacity"><xsl:value-of select="col[@field='Load Capacity']"/></data>
            <data field="max_height"><xsl:value-of select="col[@field='Max Height']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
