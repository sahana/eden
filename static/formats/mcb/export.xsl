<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
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

    <xsl:param name="resources"/>
    <xsl:param name="domains"/>
    <xsl:param name="default_domain">sahana</xsl:param>

    <!-- ****************************************************************** -->
    <!-- ROOT -->
    
    <xsl:template match="/">
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- S3XML -->
    
    <xsl:template match="s3xml">
        <ArrayOfStreamItem>
            <xsl:apply-templates select="./resource[@name='project_task' or
                                                    @name='cms_post' or
                                                    @name='event_incident']"/>
        </ArrayOfStreamItem>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- STREAM ITEM: project_task -->

    <xsl:template match="resource[@name='project_task']">
        <StreamItem>
            <Id>0</Id>
            <xsl:call-template name="TimeStamps"/>
            <ContentType>text/html</ContentType>
            <xsl:call-template name="ProjectTaskBody"/>
            <xsl:apply-templates select="reference[@field='location_id'][1]"/>
            <CultureInfo>en-US</CultureInfo>
            <xsl:call-template name="SystemInfo"/>
            <OriginationId><xsl:value-of select="@uuid"/></OriginationId>
            <xsl:call-template name="TagList"/>
        </StreamItem>
    </xsl:template>

    <xsl:template match="resource[@name='project_task' and @deleted='True']">
        <StreamItem>
            <Id>0</Id>
            <OriginationId><xsl:value-of select="@uuid"/></OriginationId>
            <Action>delete</Action>
        </StreamItem>
    </xsl:template>

    <xsl:template name="ProjectTaskBody">
        <xsl:variable name="title">
            <xsl:value-of select="data[@field='name']/text()"/>
        </xsl:variable>
        <xsl:variable name="description">
            <xsl:value-of select="data[@field='description']/text()"/>
        </xsl:variable>
        <xsl:variable name="source_url">
            <xsl:choose>
                <xsl:when test="data[@field='source_url']/text()!=''">
                    <xsl:value-of select="data[@field='source_url']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="@url"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <Body>
            &lt;p&gt;&lt;b&gt;<xsl:value-of select="$title"/>&lt;/b&gt;&lt;/p&gt;
            <xsl:if test="$description!=''">
                &lt;p&gt;<xsl:value-of select="$description"/>&lt;/p&gt;
            </xsl:if>
            <xsl:if test="$source_url!=''">
                &lt;p&gt;&lt;a href=&quot;<xsl:value-of select="$source_url"/>&quot;&gt;Link&lt;/a&gt;&lt;/p&gt;
            </xsl:if>
        </Body>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- STREAM ITEM: cms_post -->

    <xsl:template match="resource[@name='cms_post']">
        <StreamItem>
            <Id>0</Id>
            <xsl:call-template name="TimeStamps"/>
            <ContentType>text/html</ContentType>
            <xsl:call-template name="CMSPostBody"/>
            <xsl:apply-templates select="reference[@field='location_id'][1]"/>
            <CultureInfo>en-US</CultureInfo>
            <xsl:call-template name="SystemInfo"/>
            <OriginationId><xsl:value-of select="@uuid"/></OriginationId>
            <xsl:call-template name="TagList"/>
        </StreamItem>
    </xsl:template>

    <xsl:template match="resource[@name='cms_post' and @deleted='True']">
        <StreamItem>
            <Id>0</Id>
            <OriginationId><xsl:value-of select="@uuid"/></OriginationId>
            <Action>delete</Action>
        </StreamItem>
    </xsl:template>

    <xsl:template name="CMSPostBody">
        <xsl:variable name="title">
            <xsl:value-of select="data[@field='title']/text()"/>
        </xsl:variable>
        <xsl:variable name="body">
            <xsl:value-of select="data[@field='body']/text()"/>
        </xsl:variable>
        <!--
        <xsl:variable name="source_url">
            <xsl:choose>
                <xsl:when test="data[@field='source_url']/text()!=''">
                    <xsl:value-of select="data[@field='source_url']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="@url"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        -->
        <Body>
            <xsl:if test="$title!=''">
                &lt;p&gt;&lt;b&gt;<xsl:value-of select="$title"/>&lt;/b&gt;&lt;/p&gt;
            </xsl:if>
            <xsl:if test="$body!=''">
                &lt;div&gt;<xsl:value-of select="$body"/>&lt;/div&gt;
            </xsl:if>
            <!--
            <xsl:if test="$source_url!=''">
                &lt;p&gt;&lt;a href=&quot;<xsl:value-of select="$source_url"/>&quot;&gt;Link&lt;/a&gt;lt;/p&gt;
            </xsl:if>
            -->
        </Body>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- STREAM ITEM: event_incident -->

    <xsl:template match="resource[@name='event_incident']">
        <StreamItem>
            <Id>0</Id>
            <xsl:call-template name="TimeStamps"/>
            <ContentType>text/html</ContentType>
            <xsl:call-template name="EventIncidentBody"/>
            <xsl:apply-templates select="reference[@field='location_id'][1]"/>
            <CultureInfo>en-US</CultureInfo>
            <xsl:call-template name="SystemInfo"/>
            <OriginationId><xsl:value-of select="@uuid"/></OriginationId>
            <xsl:call-template name="TagList"/>
        </StreamItem>
    </xsl:template>

    <xsl:template match="resource[@name='event_incident' and @deleted='True']">
        <StreamItem>
            <Id>0</Id>
            <OriginationId><xsl:value-of select="@uuid"/></OriginationId>
            <Action>delete</Action>
        </StreamItem>
    </xsl:template>

    <xsl:template name="EventIncidentBody">
        <xsl:variable name="title">
            <xsl:value-of select="data[@field='name']/text()"/>
        </xsl:variable>
        <xsl:variable name="description">
            <xsl:value-of select="data[@field='comments']/text()"/>
        </xsl:variable>
        <!--
        <xsl:variable name="source_url">
            <xsl:choose>
                <xsl:when test="data[@field='source_url']/text()!=''">
                    <xsl:value-of select="data[@field='source_url']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="@url"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        -->
        <Body>
            <xsl:if test="$title!=''">
                &lt;p&gt;&lt;b&gt;<xsl:value-of select="$title"/>&lt;/b&gt;&lt;/p&gt;
            </xsl:if>
            <xsl:if test="$description!=''">
                &lt;p&gt;<xsl:value-of select="$description"/>&lt;/p&gt;
            </xsl:if>
            <!--
            <xsl:if test="$source_url!=''">
                &lt;p&gt;&lt;a href=&quot;<xsl:value-of select="$source_url"/>&quot;&gt;Link&lt;/a&gt;lt;/p&gt;
            </xsl:if>
            -->
        </Body>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- TimeStamps -->

    <xsl:template name="TimeStamps">
        <CreateDateTime><xsl:value-of select="@created_on"/></CreateDateTime>
        <LastUpdateDateTime><xsl:value-of select="@modified_on"/></LastUpdateDateTime>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- SYSTEM INFO: Sender and Data Source Identification -->
    
    <xsl:template name="SystemInfo">
        <xsl:variable name="resource_prefix" select="concat('[', @name, ':')"/>
        <xsl:variable name="resource_id">
            <xsl:if test="contains($resources, $resource_prefix)">
                <xsl:value-of select="substring-before(substring-after($resources, $resource_prefix), ']')"/>
            </xsl:if>
        </xsl:variable>
        <xsl:variable name="origin">
            <xsl:choose>
                <xsl:when test="contains(@uuid, '/')">
                    <xsl:value-of select="substring-before(@uuid, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$default_domain"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="domain_prefix" select="concat('[', $origin, ':')"/>
        <xsl:variable name="default_domain_prefix" select="concat('[', $default_domain, ':')"/>
        <xsl:variable name="domain_id">
            <xsl:choose>
                <xsl:when test="contains($domains, $domain_prefix)">
                    <xsl:value-of select="substring-before(substring-after($domains, $domain_prefix), ']')"/>
                </xsl:when>
                <xsl:when test="contains($domains, $default_domain_prefix)">
                    <xsl:value-of select="substring-before(substring-after($domains, $default_domain_prefix), ']')"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>
        <SystemInfo>
            <xsl:if test="$domain_id!=''">
                <SystemId>
                    <xsl:value-of select="$domain_id"/>
                </SystemId>
            </xsl:if>
            <xsl:if test="$origin!=''">
                <SystemDescription>
                    <xsl:value-of select="$origin"/>
                </SystemDescription>
            </xsl:if>
            <xsl:if test="$resource_id!=''">
                <DataSourceId>
                    <xsl:value-of select="$resource_id"/>
                </DataSourceId>
            </xsl:if>
            <DataSourceDescription>
                <xsl:value-of select="@name"/>
            </DataSourceDescription>
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
    
    <xsl:template match="reference[@field='location_id']">
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
