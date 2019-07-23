<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Targets - CSV Import Stylesheet

         CSV fields:
         Name....................dc_target.name
         Template................dc_template.name
         Status..................dc_target.status
         Project.................project_project.name (Optional link to Project)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="template" match="row" use="col[@field='Template']"/>
    <xsl:key name="project" match="row" use="col[@field='Project']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Templates -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('template',
                                                                       col[@field='Template'])[1])]">
                <xsl:call-template name="Template"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('project',
                                                                       col[@field='Project'])[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <!-- Targets -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="project" select="col[@field='Project']/text()"/>
        <xsl:variable name="status" select="col[@field='Status']/text()"/>

        <resource name="dc_target">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>

            <xsl:if test="$status!=''">
                <!-- @ToDo: Support represented text values as well as raw integers -->
                <data field="status"><xsl:value-of select="$status"/></data>
            </xsl:if>

            <!-- Link to Template -->
            <reference field="template_id" resource="dc_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>
           
            <xsl:if test="$project!=''">
                <resource name="project_project_target">
                    <!-- Link to Project -->
                    <reference field="project_id" resource="project_project">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$project"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Template">
        <xsl:variable name="template" select="col[@field='Template']/text()"/>

        <resource name="dc_template">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$template"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$template"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="project" select="col[@field='Project']/text()"/>

        <xsl:if test="$project!=''">
            <resource name="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$project"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$project"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
