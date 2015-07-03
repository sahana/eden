<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CAP Warning Priority - CSV Import Stylesheet

         CSV column...........Format..........Content

		 priority_rank........integer.........Warning Priority for Event
         event_code...........number..........CAP Warning Code
         name.................string..........CAP Warning Name
         event_type...........string..........Type of the Event
         urgency..............string..........Urgency Status
         severity.............string..........Severity Status
         certainty............string..........Certainty Status
         color_code...........date............Color Code for the warning

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="cap_warning_priority">
            <data field="priority_rank">
        	    <xsl:value-of select="col[@field='priority_rank']"/>
            </data>
            <data field="event_code"><xsl:value-of select="col[@field='event_code']"/></data>
            <data field="name"><xsl:value-of select="col[@field='name']"/></data>
            <data field="event_type"><xsl:value-of select="col[@field='event_type']"/></data>
            <data field="urgency"><xsl:value-of select="col[@field='urgency']"/></data>
            <data field="severity"><xsl:value-of select="col[@field='severity']"/></data>
            <data field="certainty"><xsl:value-of select="col[@field='certainty']"/></data>
            <data field="color_code"><xsl:value-of select="col[@field='color_code']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
