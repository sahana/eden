<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://schemas.datacontract.org/2004/07/PortfolioAPI.Models"
  xmlns:d3p1="http://schemas.datacontract.org/2004/07/System.Globalization"
  xmlns:i="http://www.w3.org/2001/XMLSchema-instance">

    <!-- **********************************************************************

         Mariner CommandBridge Export Templates

         Copyright (c) 2014 Sahana Software Foundation

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

    <xsl:param name="system_id"/>
    <xsl:param name="source_id"/>
    <xsl:param name="source_description"/>

    <!-- ****************************************************************** -->
    <!-- ROOT -->
    
    <xsl:template match="/">
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- S3XML -->
    
    <xsl:template match="s3xml">
        <ArrayOfStreamItem>
            <xsl:apply-templates select="./resource[@name='project_task']"/>
        </ArrayOfStreamItem>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- STREAM ITEM: project_task -->
    
    <xsl:template match="resource[@name='project_task']">
        <StreamItem>
            <xsl:call-template name="TimeStamps"/>
            <Id>0</Id>
            <OriginationId><xsl:value-of select="@uuid"/></OriginationId>
            <xsl:call-template name="SystemInfo"/>
            <CultureInfo>
                <d3p1:m_name>en-US</d3p1:m_name>
            </CultureInfo>
            <ContentType>text/html</ContentType>
            <xsl:call-template name="Body"/>
            <xsl:apply-templates select="reference[@field='location_id'][1]"/>
        </StreamItem>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- TimeStamps -->

    <xsl:template name="TimeStamps">
        <CreatedDateTime><xsl:value-of select="@created_on"/></CreatedDateTime>
        <LastUpdateDateTime><xsl:value-of select="@modified_on"/></LastUpdateDateTime>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- BODY: @todo -->
    
    <xsl:template name="Body">
        <Body>&lt;p&gt;&lt;b&gt;title of item&lt;/b&gt;&lt;/p&gt;&lt;p&gt;decription of item with a &lt;a href="themarinergroup.net"&gt;url&lt;/a&gt;</Body>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- SYSTEM INFO: Sender and Data Source Identification -->
    
    <xsl:template name="SystemInfo">
        <SystemInfo>
            <SystemId><xsl:value-of select="$system_id"/></SystemId>
            <SystemDescription>Sahana</SystemDescription>
            <DataSourceDescription><xsl:value-of select="$source_description"/></DataSourceDescription>
            <DataSourceId><xsl:value-of select="$source_id"/></DataSourceId>
        </SystemInfo>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- TAG LIST: @todo -->
    
    <xsl:template name="TagList">
        <TagList>
<!--             <d3p1:string>News</d3p1:string> -->
<!--             <d3p1:string>Incident</d3p1:string> -->
<!--             <d3p1:string>Marine</d3p1:string> -->
<!--             <d3p1:string>Seattle</d3p1:string> -->
        </TagList>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- Task Location -->
    
    <xsl:template match="project_task/reference[@field='location_id']">
        <xsl:if test="@lat!='' and @lon!=''">
            <Geo>
                <Latitude><xsl:value-of select="@lat"/></Latitude>
                <Longitude><xsl:value-of select="@lon"/></Longitude>
                <Altitude>0.0</Altitude>
            </Geo>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hide everything else -->
    <xsl:template match="*"/>
    
    <!-- ****************************************************************** -->
    
</xsl:stylesheet>
