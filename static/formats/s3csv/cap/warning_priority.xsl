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
    <!-- Indexes for faster processing -->
    <xsl:key name="eventtype" match="row"
             use="concat('EventType:', col[@field='Event Type'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Event Type -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('eventtype',
                                                        concat('EventType:',
                                                               col[@field='Event Type']))[1])]">
                <xsl:call-template name="EventType"/>
            </xsl:for-each>
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
            <data field="urgency"><xsl:value-of select="col[@field='Urgency']"/></data>
            <data field="severity"><xsl:value-of select="col[@field='Severity']"/></data>
            <data field="certainty"><xsl:value-of select="col[@field='Certainty']"/></data>
            <data field="color_code"><xsl:value-of select="col[@field='Color Code']"/></data>
            <xsl:variable name="EventTypeName" select="col[@field='Event Type']"/>
            <xsl:if test="$EventTypeName!=''">
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('EventType:', $EventTypeName)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="EventType">
    
        <xsl:variable name="EventTypeName" select="col[@field='Event Type']/text()"/>
        
        <resource name="event_event_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('EventType:', $EventTypeName)"/>
            </xsl:attribute>
            <data field="name">
                <xsl:value-of select="$EventTypeName"/>
            </data>
        </resource>
        
    </xsl:template>
    
    <!-- ****************************************************************** -->

</xsl:stylesheet>
