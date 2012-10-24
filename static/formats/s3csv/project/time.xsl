<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Tasks (Requirements) - CSV Import Stylesheet

         CSV column...........Format..........Content

         Task.................string..........Time Task name
         Date.................datetime........Time datetime
         Person...............string..........Time
         Hours................double..........Time hours
         Comments.............string..........Time comment

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:key name="task" match="row" use="col[@field='Task']"/>
    <xsl:key name="person" match="row" use="col[@field='Person']"/>
    
    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Tasks -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('task',
                                                                   col[@field='Task'])[1])]">
                <xsl:call-template name="Task"/>
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('person',
                                                                   col[@field='Person'])[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Times -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Task" select="col[@field='Task']/text()"/>
        <xsl:variable name="Date" select="col[@field='Date']/text()"/>
        <xsl:variable name="Person" select="col[@field='Person']/text()"/>
        <xsl:variable name="Hours" select="col[@field='Hours']/text()"/>
        <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>

        <resource name="project_time">
            <reference field="task_id" resource="project_task">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Task"/>
                </xsl:attribute>
            </reference>
            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Person"/>
                </xsl:attribute>
            </reference>
            <data field="hours"><xsl:value-of select="$Hours"/></data>
            <data field="datetime"><xsl:value-of select="$Date"/></data>
            <data field="comments"><xsl:value-of select="$Comments"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Task">
        <xsl:variable name="Task" select="col[@field='Task']/text()"/>

        <xsl:if test="$Task!=''">
            <resource name="project_task">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Task"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Task"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="Person" select="col[@field='Person']/text()"/>

        <xsl:if test="$Person!=''">
            <resource name="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Person"/>
                </xsl:attribute>
                <data field="initials"><xsl:value-of select="$Person"/></data>
            </resource>
        </xsl:if>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
