<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- Project -->

    <!-- project_task -->
    <xsl:template match="resource[@name='project_task']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='name']/text()"/>
        </title>
        <description>
            <xsl:text>Description: </xsl:text>
            <xsl:value-of select="./data[@field='description']/text()"/>
            &lt;br/&gt;
            <xsl:text>Project: </xsl:text>
            <xsl:choose>
                <xsl:when test="./resource[@name='project_task_project']/reference[@field='project_id']/text()">
                    <xsl:value-of select="./resource[@name='project_task_project']/reference[@field='project_id']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>-</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./data[@field='status']/text()">
                    <xsl:value-of select="./data[@field='status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>-</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Tag: </xsl:text>
            <xsl:choose>
                <xsl:when test="./resource[@name='project_task_tag']">
                    <xsl:for-each select="./resource[@name='project_task_tag']">
                        <xsl:value-of select="reference[@field='tag_id']/text()"/>
                            <xsl:if test="position() != last()">
                                <xsl:text>,</xsl:text>
                            </xsl:if>
                    </xsl:for-each>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>-</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </description>
    </xsl:template>

    <!-- project_comment -->
    <xsl:template match="resource[@name='project_comment']" mode="contents">
        <title>
            <xsl:value-of select="./reference[@field='task_id']/text()"/>
        </title>
        <description>
            <xsl:value-of select="@created_by"/>
            <xsl:text>: </xsl:text>
            <xsl:value-of select="./data[@field='body']/text()"/>
        </description>
    </xsl:template>
    
</xsl:stylesheet>
