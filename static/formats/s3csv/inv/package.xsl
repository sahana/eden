<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Packages - CSV Import Stylesheet

         CSV column...........Format..........Content

         Type.................string..........Package Type: PALLET or BOX
         Name.................string..........Package Name
         Width................float...........Width (m)
         Length...............float...........Length (m)
         Depth................float...........Depth (m)
         Weight...............float...........Weight (kg)
         Load Capacity........float...........Load Capacity (kg)
         Max Height...........float...........Max Height (m)
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Type">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Type']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="inv_package">
            <data field="type"><xsl:value-of select="$Type"/></data>
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
