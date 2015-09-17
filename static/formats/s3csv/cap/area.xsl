<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
         CAP Area template - CSV Import Stylesheet

         CSV column..................Format.............Content

         Area Description............string.............CAP Area Template Description
         Event Type..................string.............CAP Area Template Event Type
         Priority....................string.............CAP Area Template Priority(@ToDo?)
         Altitude....................number.............CAP Area Template Altitude (WGS in meter)
         Ceiling.....................number.............CAP Area Template Ceiling (WGS in meter)
         Area Tag..............list:key-value pair......CAP Area Template Tag 
                                                        ([{"ZIP":"00977"},{"KEY":"VALUE"}])
         Country.....................optional...........gis_location.L0 Name or ISO2
         L1..........................optional...........gis_location.L1
         L2..........................optional...........gis_location.L2
         L3..........................optional...........gis_location.L3
         L4..........................optional...........gis_location.L4 (not commonly-used)
         L5..........................optional...........gis_location.L5 (not commonly-used)
         WKT.........................WKT................gis_location.WKT (Polygon)

    *********************************************************************** -->  
    <xsl:output method="xml"/>
    
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>
    
    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Country">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Country</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>
    
    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    
    <xsl:key name="L0" match="row"
             use="col[contains(
                      document('../labels.xml')/labels/column[@name='Country']/match/text(),
                      concat('|', @field, '|'))]"/>
                      
    <xsl:key name="L1" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'])"/>
                         
    <xsl:key name="L2" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', 
                         col[@field='L1'], '/',
                         col[@field='L2'])"/>
                         
    <xsl:key name="L3" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', 
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'])"/>
                         
    <xsl:key name="L4" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', 
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'])"/>

    <xsl:key name="L5" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', 
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'], '/',
                         col[@field='L5'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
        
            <!-- L0 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L0',
                                                                   col[contains(
                                                                       document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                       concat('|', @field, '|'))])[1])]">
                <xsl:call-template name="L0"/>
            </xsl:for-each>
        
            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L1',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1']))[1])]">
                <xsl:call-template name="L1"/>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L2',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2']))[1])]">
                <xsl:call-template name="L2"/>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L3',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3']))[1])]">
                <xsl:call-template name="L3"/>
            </xsl:for-each>
            
            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L4',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4']))[1])]">
                <xsl:call-template name="L4"/>
            </xsl:for-each>

            <!-- L5 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L5',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4'], '/',
                                                                          col[@field='L5']))[1])]">
                <xsl:call-template name="L5"/>
            </xsl:for-each>
            
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
    
        <xsl:variable name="is_template">
            <xsl:text>true</xsl:text>
        </xsl:variable>
        
        <resource name="cap_area">
            <!-- Used for CAP Area Template -->
            <data field="is_template">
                <xsl:attribute name="value">
                    <xsl:value-of select="$is_template"/>
                </xsl:attribute>
            </data>
            <!-- Area Description -->
            <xsl:variable name="area_description" select="col[@field='Area Description']"/>
            <xsl:if test="$area_description!=''">
                <data field="name">
                    <xsl:value-of select="$area_description"/>
                </data>
            </xsl:if>
            <!-- Altitude -->
            <xsl:variable name="altitude" select="col[@field='Altitude']"/>
            <xsl:if test="$altitude!=''">
                <data field="altitude">
                    <xsl:attribute name="value">
                        <xsl:value-of select="$altitude"/>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <!-- Ceiling -->
            <xsl:variable name="ceiling" select="col[@field='Ceiling']"/>
            <xsl:if test="$ceiling!=''">
                <data field="ceiling">
                    <xsl:attribute name="value">
                        <xsl:value-of select="$ceiling"/>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <!-- Event Type -->
            <xsl:variable name="event_type" select="col[@field='Event Type']"/>
            <xsl:if test="$event_type!=''">
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$event_type"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <!-- Priority -->
            <!-- @ToDo: Fix Priority reference" -->
            <!--
            <xsl:variable name="priority" select="col[@field='Priority']"/>
            <xsl:if test="$priority!=''">
                <reference field="priority" resource="cap_warning_priority">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$priority"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            -->
            
            <!-- CAP Area Tag -->
            <xsl:variable name="AreaTag" select="col[@field='Area Tag']"/>
            <xsl:variable name="AreaTag-string">
                <xsl:value-of select="translate($AreaTag, '[{}]', '')"/>
            </xsl:variable>
            <xsl:if test="$AreaTag-string!=''">
                <xsl:call-template name="area-tag-builder">
                    <xsl:with-param name="area-tag">
                        <xsl:value-of select="$AreaTag-string"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:if>
            
            <!-- Link to Location -->
            <xsl:if test="col[@field='WKT']!='' or col[@field='Country']!=''">
                <resource name="cap_area_location" alias="location">
                    <xsl:call-template name="LocationReference"/>
                </resource>
            </xsl:if>
        </resource>
        
        <!-- Event Type -->
        <xsl:variable name="event_type" select="col[@field='Event Type']"/>
        <xsl:if test="$event_type!=''">
            <xsl:call-template name="EventType">
                <xsl:with-param name="EventTypeName">
                    <xsl:value-of select="$event_type"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        
        <!-- Polygon -->
        <xsl:if test="col[@field='WKT']!='' or col[@field='Country']!=''">
            <resource name="gis_location">
                <xsl:call-template name="Location"/>
            </resource>
        </xsl:if>
        
        <!-- Warning Priority -->
        <!--<xsl:variable name="priority" select="col[@field='Priority']"/>
        <xsl:if test="$priority!=''">
            <xsl:call-template name="Priority">
                <xsl:with-param name="Priority">
                    <xsl:value-of select="$priority"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>-->
    
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="EventType">
        
        <xsl:param name="EventTypeName"/>
        
        <resource name="event_event_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$EventTypeName"/>
            </xsl:attribute>
            <data field="name">
                <xsl:value-of select="$EventTypeName"/>
            </data>
        </resource>
        
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <xsl:template name="area-tag-builder">
        
        <xsl:param name="area-tag"/>
        <xsl:param name="sep" select="','"/>
        <xsl:param name="tag-sep" select="':'"/>
        
        <xsl:if test="$tag-sep">
            <xsl:choose>
                <xsl:when test="contains($area-tag, $sep) and contains($area-tag, $tag-sep)">
                    <xsl:variable name="key">
                        <xsl:value-of select="substring-before(substring-before($area-tag, $sep), $tag-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="value">
                        <xsl:value-of select="substring-after(substring-before($area-tag, $sep), $tag-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="tail">
                        <xsl:value-of select="substring-after($area-tag, $sep)"/>
                    </xsl:variable>
                    <resource name="cap_area_tag" alias="tag">
                        <data field="tag">
                            <xsl:value-of select="normalize-space(translate($key, '&quot;', ''))"/>
                        </data>
                        <data field="value">
                            <xsl:value-of select="normalize-space(translate($value, '&quot;', ''))"/>
                        </data>
                    </resource>
                    <xsl:call-template name="area-tag-builder">
                        <xsl:with-param name="area-tag" select="$tail"/>
                        <xsl:with-param name="sep" select="$sep"/>
                        <xsl:with-param name="tag-sep" select="$tag-sep"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="key">
                        <xsl:value-of select="substring-before($area-tag, $tag-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="value">
                        <xsl:value-of select="substring-after($area-tag, $tag-sep)"/>
                    </xsl:variable>
                    <resource name="cap_area_tag" alias="tag">
                        <data field="tag">
                            <xsl:value-of select="normalize-space(translate($key, '&quot;', ''))"/>
                        </data>
                        <data field="value">
                            <xsl:value-of select="normalize-space(translate($value, '&quot;', ''))"/>
                        </data>
                    </resource>                    
                </xsl:otherwise>
            </xsl:choose>
        
        </xsl:if>        
    
    </xsl:template>

    <!-- ****************************************************************** -->
    <!--<xsl:template name="Priority">
        
        <xsl:param name="Priority"/>
        
        <resource name="cap_warning_priority">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Priority"/>
            </xsl:attribute>
            <data field="name">
                <xsl:value-of select="$Priority"/>
            </data>
        </resource>
        
    </xsl:template>-->
    
    <!-- ****************************************************************** -->
    <xsl:template name="L0">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>

        <xsl:if test="$l0!=''">
        
            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
            
            <!-- Create the gis location -->
            
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                </xsl:attribute>
            
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L1'] or col[@field='L2'] or col[@field='L3'] or col[@field='L4'] or col[@field='L5']">
                    </xsl:when>
                    <xsl:otherwise>
                        <data field="name"><xsl:value-of select="$l0"/></data>
                        <data field="level"><xsl:text>L0</xsl:text></data>
                        <data field="gis_feature_type"><xsl:text>1</xsl:text></data>
                        <xsl:choose>
                            <xsl:when test="col[@field='WKT']!=''">
                                <data field="wkt"><xsl:value-of select="col[@field='WKT']"/></data>                                
                            </xsl:when>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:if test="col[@field='L1']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <!-- Parent to Country -->
                <xsl:if test="$countrycode!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:if test="col[@field='L2']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:if test="col[@field='L3']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:if test="col[@field='L4']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>
    
    <!-- ****************************************************************** -->
    <xsl:template name="L5">
        <xsl:if test="col[@field='L5']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>
            <xsl:variable name="l5" select="col[@field='L5']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l5"/></data>
                <data field="level"><xsl:text>L5</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L4']!=''">
                        <!-- Parent to L4 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>
   
    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">

        <xsl:variable name="wkt" select="col[@field='WKT']/text()"/>

        <xsl:choose>
            <xsl:when test="$wkt!=''">
                <!-- Specific Location -->
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$wkt"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>

            <xsl:otherwise>
                <!-- Lx -->
                <xsl:variable name="l0" select="col[@field='Country']/text()"/>
                <xsl:variable name="l1" select="col[@field='L1']/text()"/>
                <xsl:variable name="l2" select="col[@field='L2']/text()"/>
                <xsl:variable name="l3" select="col[@field='L3']/text()"/>
                <xsl:variable name="l4" select="col[@field='L4']/text()"/>
                <xsl:variable name="l5" select="col[@field='L5']/text()"/>

                <!-- Country Code = UUID of the L0 Location -->
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="string-length($l0)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string">
                                   <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <xsl:variable name="l1id" select="concat('L1/', $countrycode, '/', $l1)"/>
                <xsl:variable name="l2id" select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                <xsl:variable name="l3id" select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                <xsl:variable name="l4id" select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                <xsl:variable name="l5id" select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>

                <xsl:choose>
                    <xsl:when test="$l5!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l5id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l4!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l4id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l3!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l3id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l0!=''">
                        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                        <reference field="location_id" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Location">

        <xsl:variable name="Name" select="col[@field='Area Description']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
        <xsl:variable name="wkt" select="col[@field='WKT']/text()"/>

        <!-- Country Code = UUID of the L0 Location -->
        <xsl:variable name="countrycode">
            <xsl:choose>
                <xsl:when test="string-length($l0)!=2">
                    <xsl:call-template name="countryname2iso">
                        <xsl:with-param name="country">
                            <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                           <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <xsl:variable name="l1id" select="concat('L1/', $countrycode, '/', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>

        <!-- CAP Area Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:choose>
                    <xsl:when test="$wkt!=''">
                        <xsl:value-of select="$wkt"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l5!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l5id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l4id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l3id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l2id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l1id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:otherwise>
            </xsl:choose>
            <data field="name"><xsl:value-of select="$Name"/></data>
            <xsl:choose>
                <xsl:when test="$wkt!=''">
                    <data field="wkt"><xsl:value-of select="$wkt"/></data>
                </xsl:when>
            </xsl:choose>
        </resource>

    </xsl:template>
    
</xsl:stylesheet>
