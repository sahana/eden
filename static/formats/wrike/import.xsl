<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         Wrike Import Templates

         Copyright (c) 2010 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    
    <!-- ****************************************************************** -->
    <!-- Root template -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="wrike-data"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="wrike-data">
        <xsl:apply-templates select="account|folder|task"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ACCOUNT                                                            -->
    <!-- ****************************************************************** -->
    <xsl:template match="account">
        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('wrike/', @id)"/>
            </xsl:attribute>
            <xsl:apply-templates select="*"/>
        </resource>
    </xsl:template>

    <xsl:template match="account/name">
        <data field="name"><xsl:value-of select="text()"/></data>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- FOLDER                                                             -->
    <!-- ****************************************************************** -->
    <xsl:template match="folder">
        <resource name="event_incident">
            <xsl:attribute name="uuid">
                <xsl:value-of select="concat('wrike/', @id)"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="@deleted='True'">
                    <xsl:attribute name="deleted">True</xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="*"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:apply-templates select="*"/>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="folder/title">
        <data field="name"><xsl:value-of select="text()"/></data>
    </xsl:template>

    <!-- ****************************************************************** 
    The Account ID will be the same for all 
    <xsl:template match="folder/accountId">
        <reference field="organisation_id" resource="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('wrike/', text())"/>
            </xsl:attribute>
        </reference>
    </xsl:template>
    -->
    <!-- ****************************************************************** -->
    <!-- TASK                                                               -->
    <!-- ****************************************************************** -->
    <xsl:template match="task">
        <resource name="project_task">
            <xsl:attribute name="uuid">
                <xsl:value-of select="concat('wrike/', @id)"/>
            </xsl:attribute>
            <xsl:if test="createdDate/text() != ''">
                <xsl:attribute name="created_on">
                    <xsl:value-of select="createdDate/text()"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="updatedDate/text() != ''">
                <xsl:attribute name="modified_on">
                    <xsl:value-of select="updatedDate/text()"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="@deleted='True'">
                    <xsl:attribute name="deleted">True</xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="*"/>
                </xsl:otherwise>
            </xsl:choose>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="task/title">
        <data field="name"><xsl:value-of select="text()"/></data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="task/description">
        <data field="description"><xsl:value-of select="text()"/></data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="task/dueDate">
        <data field="date_due"><xsl:value-of select="text()"/></data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="task/parentId">
        <resource name="event_task">
            <reference field="incident_id" resource="event_incident">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="concat('wrike/', text())"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="task/status">
        <data field="status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="text()='Active'">2</xsl:when>
                    <xsl:when test="text()='Deferred'">6</xsl:when>
                    <xsl:when test="text()='Cancelled'">7</xsl:when>
                    <xsl:when test="text()='Completed'">12</xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <xsl:template match="task/importance">
        <data field="priority">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="text()='High'">2</xsl:when>
                    <xsl:when test="text()='Normal'">3</xsl:when>
                    <xsl:when test="text()='Low'">4</xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="task/permalink">
        <data field="source_url">
            <xsl:value-of select="text()"/>
        </data>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- Hide everything else -->
    <xsl:template match="*"/>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
