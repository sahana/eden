<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CAP Warning Priority - CSV Import Stylesheet

         CSV column...........Format..........Content
         Priority Rank........integer.........Warning Priority for Event
         Event Code...........number..........CAP Warning Code
         Name.................string..........CAP Warning Name
         Event Type...........string..........Type of the Event
         Urgency..............string..........Urgency Status
         Severity.............string..........Severity Status
         Certainty............string..........Certainty Status
         Color Code...........string..........Color Code for the warning

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
        	    <xsl:value-of select="col[@field='Priority Rank']"/>
            </data>
            <data field="event_code"><xsl:value-of select="col[@field='Event Code']"/></data>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="event_type"><xsl:value-of select="col[@field='Event Type']"/></data>
            <data field="urgency"><xsl:value-of select="col[@field='Urgency']"/></data>
            <data field="severity"><xsl:value-of select="col[@field='Severity']"/></data>
            <data field="certainty"><xsl:value-of select="col[@field='Certainty']"/></data>
            <data field="color_code"><xsl:value-of select="col[@field='Color Code']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
