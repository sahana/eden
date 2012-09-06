<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:cap = "urn:oasis:names:tc:emergency:cap:1.2">

    <!-- **********************************************************************

         CAP Import Templates for S3XRC

         Copyright (c) 2011 Sahana Software Foundation

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
    <xsl:output method="xml" indent="yes"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="cap:alert"/>
        </s3xml>
    </xsl:template>

    <!-- util -->
    <xsl:include href="../xml/commons.xsl"/>

    <!-- key-value named template -->
    <xsl:template match="cap:alert/code">
        <xsl:if test="cap:valueName">
            <xsl:text>{key: '</xsl:text>
            <xsl:value-of select="cap:valueName" />
            <xsl:text>', value: '</xsl:text>
            <xsl:value-of select="cap:value" />
            <xsl:text>'}, </xsl:text>
        </xsl:if>
    </xsl:template>

    <xsl:template match="cap:eventCode">
        <xsl:if test="cap:valueName">
            <xsl:text>{key: '</xsl:text>
            <xsl:value-of select="cap:valueName" />
            <xsl:text>', value: '</xsl:text>
            <xsl:value-of select="cap:value" />
            <xsl:text>'}, </xsl:text>
        </xsl:if>
    </xsl:template>

    <xsl:template match="cap:parameter">
        <xsl:if test="cap:valueName">
            <xsl:text>{key: '</xsl:text>
            <xsl:value-of select="cap:valueName" />
            <xsl:text>', value: '</xsl:text>
            <xsl:value-of select="cap:value" />
            <xsl:text>'}, </xsl:text>
        </xsl:if>
    </xsl:template>

    <xsl:template match="cap:geocode">
        <xsl:if test="cap:valueName">
            <xsl:text>{key: '</xsl:text>
            <xsl:value-of select="cap:valueName" />
            <xsl:text>', value: '</xsl:text>
            <xsl:value-of select="cap:value" />
            <xsl:text>'}, </xsl:text>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:alert">
        <s3xml>
            <resource name="cap_alert">
                <xsl:attribute name="uuid">
                    <xsl:text>urn:uuid:</xsl:text>
                    <xsl:value-of select="cap:identifier" />
                </xsl:attribute>

                <data field="identifier">
                    <xsl:value-of select="cap:identifier" />
                </data>
                <data field="sender">
                    <xsl:value-of select="cap:sender" />
                </data>
                <data field="sent">
                    <xsl:value-of select="cap:sent" />
                </data>
                <data field="status">
                    <xsl:value-of select="cap:status" />
                </data>
                <data field="msg_type">
                    <xsl:value-of select="cap:msgType" />
                </data>
                <data field="source">
                    <xsl:value-of select="cap:source" />
                </data>
                <data field="scope">
                    <xsl:value-of select="cap:scope" />
                </data>
                <data field="restriction">
                    <xsl:value-of select="cap:restriction" />
                </data>
                <data field="addresses"> <!-- further in python code -->
                    <xsl:value-of select="cap:addresses" />
                </data>
                <data field="code">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:apply-templates select="cap:alert/code" />
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
                <data field="code">
                    <xsl:attribute name="value">
                    </xsl:attribute>
                </data>
                <data field="note">
                    <xsl:value-of select="cap:note" />
                </data>

                <!-- below two fields are further parsed in python code -->
                <data field="references">
                    <xsl:value-of select="cap:references" />
                </data>
                <data field="incidents">
                    <xsl:value-of select="cap:incidents" />
                </data>

                <xsl:apply-templates select="./cap:info" />
            </resource>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:info">
        <resource name="cap_info">
                <data field="language">
                    <xsl:value-of select="cap:language" />
                </data>
                <data field="category">
                    <xsl:value-of select="cap:category" />
                </data>
                <data field="event">
                    <xsl:value-of select="cap:event" />
                </data>
                <data field="response_type">
                    <xsl:value-of select="cap:response_type" />
                </data>
                <!-- @todo: priority -->
                <data field="urgency">
                    <xsl:value-of select="cap:urgency" />
                </data>
                <data field="severity">
                    <xsl:value-of select="cap:severity" />
                </data>
                <data field="certainty">
                    <xsl:value-of select="cap:certainty" />
                </data>
                <data field="audience">
                    <xsl:value-of select="cap:audience" />
                </data>
                <data field="event_code">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:apply-templates select="cap:eventCode" />
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
                <data field="effective">
                    <xsl:value-of select="cap:effective" />
                </data>
                <data field="onset">
                    <xsl:value-of select="cap:onset" />
                </data>
                <data field="expires">
                    <xsl:value-of select="cap:expires" />
                </data>
                <data field="sender_name">
                    <xsl:value-of select="cap:senderName" />
                </data>
                <data field="headline">
                    <xsl:value-of select="cap:headline" />
                </data>
                <data field="description">
                    <xsl:value-of select="cap:description" />
                </data>
                <data field="instruction">
                    <xsl:value-of select="cap:instruction" />
                </data>
                <data field="web">
                    <xsl:value-of select="cap:web" />
                </data>
                <data field="contact">
                    <xsl:value-of select="cap:contact" />
                </data>
                <data field="parameter">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:apply-templates select="cap:parameter" />
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>

                <xsl:apply-templates select="cap:resource" />
                <xsl:apply-templates select="cap:area" />
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:resource">
        <resource name="cap_info_resource">
                <data field="resource_desc">
                    <xsl:value-of select="cap:resourceDesc" />
                </data>
                <data field="mime_type">
                    <xsl:value-of select="cap:mimeType" />
                </data>
                <data field="size">
                    <xsl:value-of select="cap:size" />
                </data>
                <data field="uri">
                    <xsl:value-of select="cap:uri" />
                </data>
                <data field="deref_uri">
                    <xsl:value-of select="cap:derefUri" />
                </data>
                <data field="digest">
                    <xsl:value-of select="cap:digest" />
                </data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="cap:area">
        <resource name="cap_info_area">
                <data field="area_desc">
                    <xsl:value-of select="cap:areaDesc" />
                </data>
                <!-- polygon -->
                <data field="circle">
                    <xsl:value-of select="cap:circle" />
                </data>
                <data field="geocode">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                            <xsl:apply-templates select="cap:geocode" />
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
                <data field="altitude">
                    <xsl:value-of select="cap:altitude" />
                </data>
                <data field="ceiling">
                    <xsl:value-of select="cap:ceiling" />
                </data>
         </resource>
    </xsl:template>

</xsl:stylesheet>
