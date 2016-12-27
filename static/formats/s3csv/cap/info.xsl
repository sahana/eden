<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
         CAP Info template - CSV Import Stylesheet

         CSV column..................Format.............Content

         Identifier..................string.............CAP template identifier 
                                                        Use to link with template alert
         Language....................string.............CAP template info langauge
         Category.........comma-separated string........CAP template info category
         Event Type..................string.............CAP template info event
         Response Type....comma-separated string........CAP template info response_type
         Audience....................string.............CAP template info audience
         Sender Name.................string.............CAP template info sender_name
         Headline....................string.............CAP template info headline
         Description.................string.............CAP template info description
         Instruction.................string.............CAP template info instruction
         Contact.....................string.............CAP template info contact
         Parameters..............key-value pair.........CAP template info parameter

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>
    
    <xsl:output method="xml"/>
    
    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        
        <resource name="cap_info">
            
            <!-- Link to Alert -->
            <reference field="alert_id" resource="cap_alert">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="concat('urn:capid:', col[@field='Identifier']/text())"/>
                </xsl:attribute>
            </reference>
            <!-- Language -->
            <xsl:variable name="Language" select="col[@field='Language']"/>
            <xsl:if test="$Language!=''">
                <data field="language">
                    <xsl:attribute name="value">
                        <xsl:value-of select="$Language"/>
                    </xsl:attribute>                
                </data>
            </xsl:if>
            <!-- Category -->
            <xsl:variable name="list-category-val" select="col[@field='Category']"/>
            <xsl:if test="$list-category-val!=''">
                <data field="category">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:call-template name="list-String">
                            <xsl:with-param name="list">
                                <xsl:value-of select="$list-category-val"/>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <!-- Response Type -->
            <xsl:variable name="list-response_type-val" select="col[@field='Response Type']"/>
            <xsl:if test="$list-response_type-val!=''">
                <data field="response_type">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:call-template name="list-String">
                            <xsl:with-param name="list">
                                <xsl:value-of select="$list-response_type-val"/>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <!-- Audience -->
            <xsl:variable name="Audience" select="col[@field='Audience']/text()"/>
            <xsl:if test="$Audience!=''">
                <data field="audience">
                    <xsl:value-of select="$Audience"/>
                </data>
            </xsl:if>
            <!-- Event Code -->
            <!-- Enable when we being to use this -->
            <!--<xsl:variable name="EventCode" select="col[@field='Event Code']"/>
            <xsl:variable name="EventCode-string">
                <xsl:value-of select="translate($EventCode, '[{}]', '')"/>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="$EventCode-string!=''">
                    <data field="event_code">
                        <xsl:attribute name="value">
                            <xsl:text>[</xsl:text>
                            <xsl:call-template name="key-value-String">
                                <xsl:with-param name="key-value">
                                    <xsl:value-of select="$EventCode-string"/>
                                </xsl:with-param>
                            </xsl:call-template>
                            <xsl:text>]</xsl:text>
                        </xsl:attribute>
                    </data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="event_code">
                        <xsl:attribute name="value">
                            <xsl:text>[]</xsl:text>
                        </xsl:attribute>
                    </data>
                </xsl:otherwise>
            </xsl:choose>-->
            <!-- Sender Name -->
            <xsl:variable name="SenderName" select="col[@field='Sender Name']/text()"/>
            <xsl:if test="$SenderName!=''">
                <data field="sender_name">
                    <xsl:value-of select="$SenderName"/>
                </data>
            </xsl:if>
            <!-- Headline -->
            <xsl:variable name="Headline" select="col[@field='Headline']/text()"/>
            <xsl:if test="$Headline!=''">
                <data field="headline">
                    <xsl:value-of select="$Headline"/>
                </data>
            </xsl:if>
            <!-- Description -->
            <xsl:variable name="Description" select="col[@field='Description']/text()"/>
            <xsl:if test="$Description!=''">
                <data field="description">
                    <xsl:value-of select="$Description"/>
                </data>
            </xsl:if>
            <!-- Instruction -->
            <xsl:variable name="Instruction" select="col[@field='Instruction']/text()"/>
            <xsl:if test="$Instruction!=''">
                <data field="instruction">
                    <xsl:value-of select="$Instruction"/>
                </data>
            </xsl:if>
            <!-- Contact Information -->
            <xsl:variable name="Contact" select="col[@field='Contact']/text()"/>
            <xsl:if test="$Contact!=''">
                <data field="contact">
                    <xsl:value-of select="$Contact"/>
                </data>
            </xsl:if>
            <!-- Parameter -->
            <xsl:variable name="Parameter-string" select="col[@field='Parameters']"/>
            <xsl:if test="$Parameter-string!=''">
                <xsl:call-template name="parameter-String">
                    <xsl:with-param name="key-value">
                        <xsl:value-of select="$Parameter-string"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:if>
            <!-- Event Type -->
            <xsl:variable name="EventTypeName" select="col[@field='Event Type']"/>
            <xsl:if test="$EventTypeName!=''">
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$EventTypeName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            
        </resource>
        <!-- Event Type Template call -->
        <xsl:variable name="EventTypeName" select="col[@field='Event Type']"/>
        <xsl:if test="$EventTypeName!=''">
            <xsl:call-template name="EventType">
                <xsl:with-param name="EventTypeName">
                    <xsl:value-of select="$EventTypeName"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        
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
    <xsl:template name="list-String">

        <xsl:param name="list"/>
        <xsl:param name="listsep" select="','"/>

        <xsl:if test="$listsep">
            <xsl:choose>
                <xsl:when test="contains($list, $listsep)">
                    <xsl:variable name="head">
                        <xsl:value-of select="substring-before($list, $listsep)"/>
                    </xsl:variable>
                    <xsl:variable name="tail">
                        <xsl:value-of select="substring-after($list, $listsep)"/>
                    </xsl:variable>
                    <xsl:text>"</xsl:text>
                    <xsl:value-of select="normalize-space(translate($head, '&quot;', ''))"/>
                    <xsl:text>",</xsl:text>
                    <xsl:call-template name="list-String">
                        <xsl:with-param name="list" select="$tail"/>
                        <xsl:with-param name="listsep" select="$listsep"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="normalize-space($list)!=''">
                        <xsl:text>"</xsl:text>
                        <xsl:value-of select="normalize-space(translate($list, '&quot;', ''))"/>
                        <xsl:text>"</xsl:text>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>
    
    <!-- ****************************************************************** -->
    <xsl:template name="key-value-String">
    
        <xsl:param name="key-value"/>
        <xsl:param name="sep" select="','"/>
        <xsl:param name="kv-sep" select="':'"/>
        
        <xsl:if test="$kv-sep">
            <xsl:choose>
                <xsl:when test="contains($key-value, $sep) and contains($key-value, $kv-sep)">
                    <xsl:variable name="key">
                        <xsl:value-of select="substring-before(substring-before($key-value, $sep), $kv-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="value">
                        <xsl:value-of select="substring-after(substring-before($key-value, $sep), $kv-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="tail">
                        <xsl:value-of select="substring-after($key-value, $sep)"/>
                    </xsl:variable>
                    <xsl:text>{"key":"</xsl:text>
                    <xsl:value-of select="normalize-space(translate($key, '&quot;', ''))"/>
                    <xsl:text>","value":"</xsl:text>
                    <xsl:value-of select="normalize-space(translate($value, '&quot;', ''))"/>
                    <xsl:text>"},</xsl:text>
                    <xsl:call-template name="key-value-String">
                        <xsl:with-param name="key-value" select="$tail"/>
                        <xsl:with-param name="sep" select="$sep"/>
                        <xsl:with-param name="kv-sep" select="$kv-sep"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="key">
                        <xsl:value-of select="substring-before($key-value, $kv-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="value">
                        <xsl:value-of select="substring-after($key-value, $kv-sep)"/>
                    </xsl:variable>
                    <xsl:text>{"key":"</xsl:text>
                    <xsl:value-of select="normalize-space(translate($key, '&quot;', ''))"/>
                    <xsl:text>","value":"</xsl:text>
                    <xsl:value-of select="normalize-space(translate($value, '&quot;', ''))"/>
                    <xsl:text>"}</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="parameter-String">
    
        <xsl:param name="key-value"/>
        <xsl:param name="sep" select="','"/>
        <xsl:param name="kv-sep" select="'&quot;&#58;&quot;'"/>
        
        <xsl:if test="$kv-sep">
            <xsl:choose>
                <xsl:when test="contains($key-value, $sep) and contains($key-value, $kv-sep)">
                    <xsl:variable name="head">
                        <xsl:value-of select="substring-before($key-value, $sep)"/>
                    </xsl:variable>
                    <xsl:variable name="key">
                        <xsl:value-of select="substring-before($head, $kv-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="value">
                        <xsl:value-of select="substring-after($head, $kv-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="tail">
                        <xsl:value-of select="substring-after($key-value, $sep)"/>
                    </xsl:variable>
                    <xsl:call-template name="info-parameter-construct">
                        <xsl:with-param name="key" select="normalize-space(translate($key, '&quot;', ''))"/>
                        <xsl:with-param name="value" select="normalize-space(translate($value, '&quot;', ''))"/>
                    </xsl:call-template>
                    <xsl:call-template name="parameter-String">
                        <xsl:with-param name="key-value" select="$tail"/>
                        <xsl:with-param name="sep" select="$sep"/>
                        <xsl:with-param name="kv-sep" select="$kv-sep"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="key">
                        <xsl:value-of select="substring-before($key-value, $kv-sep)"/>
                    </xsl:variable>
                    <xsl:variable name="value">
                        <xsl:value-of select="substring-after($key-value, $kv-sep)"/>
                    </xsl:variable>
                    <xsl:call-template name="info-parameter-construct">
                        <xsl:with-param name="key" select="normalize-space(translate($key, '&quot;', ''))"/>
                        <xsl:with-param name="value" select="normalize-space(translate($value, '&quot;', ''))"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="info-parameter-construct">
        
        <xsl:param name="key" />
        <xsl:param name="value" />
        
        <resource name="cap_info_parameter">
            <data field="name">
                <xsl:value-of select="$key" />
            </data>
            <data field="value">
                <xsl:value-of select="$value" />
            </data>
            <data field="mobile">
                <xsl:attribute name="value">
                    <xsl:text>true</xsl:text>
                </xsl:attribute>
            </data>
        </resource>
    </xsl:template>
    
</xsl:stylesheet>
