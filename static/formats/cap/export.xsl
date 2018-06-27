<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="urn:oasis:names:tc:emergency:cap:1.2">

    <!-- **********************************************************************
         CAP Export Templates

         Copyright (c) 2011-16 Sahana Software Foundation

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
    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="/s3xml">
        <xsl:apply-templates select="./resource[@name='cap_alert']"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- cap_alert -->
    <xsl:template match="resource[@name='cap_alert']">

        <alert>
            <identifier>
                <xsl:value-of select="data[@field='identifier']"/>
            </identifier>

            <!-- @todo: must not be empty -->
            <sender>
                <xsl:value-of select="data[@field='sender']"/>
            </sender>

            <sent>
                <xsl:call-template name="add-timezone">
                    <xsl:with-param name="time">
                        <xsl:choose>
                            <!-- @todo: ISO Format -->
                            <xsl:when test="data[@field='sent']!=''">
                                <xsl:value-of select="data[@field='sent']/@value"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="@created_on"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </sent>

            <status>
                <xsl:value-of select="translate(data[@field='status']/@value, '&quot;', '')"/>
            </status>
            <msgType>
                <xsl:value-of select="data[@field='msg_type']"/>
            </msgType>

            <xsl:if test="data[@field='source']!=''">
                <source><xsl:value-of select="data[@field='source']"/></source>
            </xsl:if>

            <scope>
                <xsl:value-of select="data[@field='scope']"/>
            </scope>

            <xsl:if test="data[@field='scope']='Restricted'">
                <restriction><xsl:value-of select="data[@field='restriction']"/></restriction>
            </xsl:if>

            <xsl:if test="data[@field='addresses']/@value!='[]'">
                <addresses>
                    <xsl:call-template name="make-space-delimited">
                        <xsl:with-param name="string">
                            <xsl:value-of select="data[@field='addresses']"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </addresses>
            </xsl:if>

            <xsl:if test="data[@field='codes']">
                <xsl:call-template name="split-into-nodes">
                    <xsl:with-param name="string"><xsl:value-of select="data[@field='codes']"/>
                    </xsl:with-param>
                    <xsl:with-param name="node-name">code</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="data[@field='note']!=''">
                <note><xsl:value-of select="data[@field='note']"/></note>
            </xsl:if>

            <xsl:if test="data[@field='reference']!=''">
            	<references>
            		<xsl:value-of select="data[@field='reference']"/>
            	</references>
            </xsl:if>

            <xsl:if test="data[@field='incidents']!=''">
                <incidents>
                    <xsl:call-template name="make-space-delimited">
                        <xsl:with-param name="string">
                            <xsl:value-of select="data[@field='incidents']"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </incidents>
            </xsl:if>

            <xsl:apply-templates select="resource[@name='cap_info']"/>
        </alert>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- cap_info -->
    <xsl:template match="resource[@name='cap_info']">
        <info>
            <xsl:variable name="info_uuid" select="@uuid"/>
            <xsl:if test="data[@field='language']!=''">
                <language><xsl:value-of select="translate(data[@field='language']/@value, '&quot;', '')"/></language>
            </xsl:if>

            <xsl:if test="data[@field='category']">
                <xsl:call-template name="split-into-nodes">
                    <xsl:with-param name="string">
                    	<xsl:value-of select="translate(data[@field='category']/@value, '&quot;][', '')"/>
                    </xsl:with-param>
                    <xsl:with-param name="node-name">category</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <event><xsl:value-of select="data[@field='event']"/></event>

            <xsl:if test="data[@field='response_type']">
                <xsl:call-template name="split-into-nodes">
                    <xsl:with-param name="string">
                    	<xsl:value-of select="translate(data[@field='response_type']/@value, '&quot;][', '')"/>
                    </xsl:with-param>
                    <xsl:with-param name="node-name">responseType</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <urgency>
            	<xsl:value-of select="translate(data[@field='urgency']/@value, '&quot;', '')"/>
            </urgency>

            <severity>
            	<xsl:value-of select="translate(data[@field='severity']/@value, '&quot;', '')"/>
            </severity>

            <certainty>
            	<xsl:value-of select="translate(data[@field='certainty']/@value, '&quot;', '')"/>
            </certainty>

            <xsl:if test="data[@field='audience']!=''">
                <audience><xsl:value-of select="data[@field='audience']"/></audience>
            </xsl:if>

            <xsl:if test="data[@field='event_code']">
                <xsl:call-template name="key-value-pairs">
                    <xsl:with-param name="string">
                        <xsl:value-of select="translate(data[@field='event_code']/@value, '&quot;[\]', '')"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">eventCode</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="data[@field='effective']">
                <effective>
                    <xsl:call-template name="add-timezone">
                        <xsl:with-param name="time">
                            <xsl:value-of select="data[@field='effective']/@value"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </effective>
            </xsl:if>

            <xsl:if test="data[@field='onset']">
                <onset>
                    <xsl:call-template name="add-timezone">
                        <xsl:with-param name="time">
                            <xsl:value-of select="data[@field='onset']/@value"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </onset>
            </xsl:if>

            <xsl:if test="data[@field='expires']">
                <expires>
                    <xsl:call-template name="add-timezone">
                        <xsl:with-param name="time">
                            <xsl:value-of select="data[@field='expires']/@value"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </expires>
            </xsl:if>

            <xsl:if test="data[@field='sender_name']!=''">
                <senderName><xsl:value-of select="data[@field='sender_name']"/></senderName>
            </xsl:if>

            <xsl:if test="data[@field='headline']!=''">
                <headline><xsl:value-of select="data[@field='headline']"/></headline>
            </xsl:if>

            <xsl:if test="data[@field='description']!=''">
                <description><xsl:value-of select="data[@field='description']"/></description>
            </xsl:if>

            <xsl:if test="data[@field='instruction']!=''">
                <instruction><xsl:value-of select="data[@field='instruction']"/></instruction>
            </xsl:if>

            <xsl:if test="data[@field='web']!=''">
                <xsl:choose>
                    <xsl:when test="@mci=1">
                        <!-- Locally created Alert => append /profile -->
                        <web><xsl:value-of select="concat(data[@field='web']/text(), '/profile')"/></web>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Imported Alert => use URL as-is -->
                        <web><xsl:value-of select="data[@field='web']/text()"/></web>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>

            <xsl:if test="data[@field='contact']!=''">
                <contact><xsl:value-of select="data[@field='contact']"/></contact>
            </xsl:if>

            <xsl:if test="reference[@field='event_type_id']!=''">
            	<parameter>
                    <valueName>sahana:event type</valueName>
                    <value><xsl:value-of select="reference[@field='event_type_id']"/></value>
                </parameter>
            </xsl:if>

            <xsl:if test="reference[@field='priority']!=''">
            	<parameter>
                    <valueName>sahana:warning priority</valueName>
                    <value><xsl:value-of select="reference[@field='priority']"/></value>
                </parameter>
            </xsl:if>

            <xsl:for-each select="../resource[@name='cap_info_parameter'][reference[@field='info_id' and @uuid=$info_uuid]]">
                <parameter>
                    <valueName>
                        <xsl:value-of select="data[@field='name']"/>
                    </valueName>
                    <value>
                        <xsl:value-of select="data[@field='value']"/>
                    </value>
                </parameter>
            </xsl:for-each>

            <!-- Not used -->
            <!--<xsl:if test="data[@field='parameter']">
                <xsl:call-template name="key-value-pairs">
                    <xsl:with-param name="string">
                        <xsl:value-of select="translate(data[@field='parameter']/@value, '&quot;[\]', '')"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">parameter</xsl:with-param>
                </xsl:call-template>
            </xsl:if>-->

            <parameter>
                <valueName>layer:tweet</valueName>
                <value>
                    <xsl:value-of select="translate(../data[@field='status']/@value, '&quot;', '')"/><xsl:text>: </xsl:text><xsl:value-of select="data[@field='headline']"/>
                    <xsl:text>&#x0A;</xsl:text>
                    <xsl:text>Sender: </xsl:text><xsl:value-of select="../data[@field='sender']"/>
                    <xsl:text>&#x0A;</xsl:text>
                    <xsl:text>Website: </xsl:text><xsl:value-of select="concat(data[@field='web'], '/profile')"/>
                </value>
            </parameter>

            <parameter>
                <valueName>layer:sms</valueName>
                <value>
                    <xsl:value-of select="translate(../data[@field='status']/@value, '&quot;', '')"/>
		    <xsl:text>&#160;</xsl:text><xsl:value-of select="translate(../data[@field='msg_type']/@value, '&quot;', '')"/>
                    <xsl:text>&#160;for&#160;</xsl:text>
		    <xsl:value-of select="../resource[@name='cap_area']/data[@field='name']"/>
		    <xsl:text>&#160;with&#160;</xsl:text>
		    <xsl:choose>
		        <xsl:when test="reference[@field='priority']!=''">
			    <xsl:value-of select="reference[@field='priority']"/>
			</xsl:when>
			<xsl:otherwise>
			    <xsl:text>Unknown</xsl:text>
			</xsl:otherwise>
		    </xsl:choose>
		    <xsl:text>&#160;priority&#160;</xsl:text>
		    <xsl:value-of select="reference[@field='event_type_id']"/>
		    <xsl:text>&#160;issued&#160;by&#160;</xsl:text>
		    <xsl:value-of select="data[@field='sender_name']"/>
		    <xsl:text>&#160;at&#160;</xsl:text>
		    <xsl:value-of select="../data[@field='sent']/@value"/>
		    <xsl:text>&#160;(ID:</xsl:text>
		    <xsl:value-of select="../data[@field='identifier']"/>
                    <xsl:text>)</xsl:text>
                </value>
            </parameter>

            <xsl:variable name="uuid" select="@uuid"/>

            <!-- Resources -->
            <!-- Include all Resources within this Info & all that are global to the Alert -->
            <xsl:apply-templates select="../resource[@name='cap_resource'][reference[@field='info_id' and @uuid=$uuid]]|
                                         ../resource[@name='cap_resource'][not(reference[@field='info_id'])]"/>

            <!-- Areas -->
            <!-- Include all Areas within this Info & all that are global to the Alert -->
            <xsl:apply-templates select="../resource[@name='cap_area'][reference[@field='info_id' and @uuid=$uuid]]|
                                         ../resource[@name='cap_area'][not(reference[@field='info_id'])]"/>
        </info>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- cap_area -->
    <xsl:template match="resource[@name='cap_area']">
        <xsl:variable name="altitude">
            <xsl:value-of select="data[@field='altitude']" />
        </xsl:variable>
        <xsl:variable name="elevation">
            <!-- @ToDo: Fix -->
            <xsl:value-of select="../resource[@name='cap_area_location']/resource[@name='gis_location']/data[@field='elevation']" />
        </xsl:variable>
        <xsl:variable name="area_uuid" select="@uuid"/>

        <area>
            <areaDesc><xsl:value-of select="data[@field='name']"/></areaDesc>

            <xsl:for-each select="../resource[@name='cap_area_location'][reference[@field='area_id' and @uuid=$area_uuid]]/reference[@field='location_id']">
                <xsl:variable name="location_uuid">
                    <xsl:value-of select="@uuid" />
                </xsl:variable>
                <xsl:apply-templates select="//resource[@name='gis_location' and @uuid=$location_uuid]" />
            </xsl:for-each>
            <!--
            <xsl:apply-templates select="resource[@name='cap_area_location']//resource[@name='gis_location_tag']" />
            -->

            <xsl:for-each select="../resource[@name='cap_area_tag'][reference[@field='area_id' and @uuid=$area_uuid]]">
            	<xsl:variable name="tag_uuid">
            		<xsl:value-of select="@uuid"/>
            	</xsl:variable>
            	<xsl:apply-templates select="//resource[@name='cap_area_tag' and @uuid=$tag_uuid]" />
            </xsl:for-each>

            <xsl:choose>
                <!-- Use the info altitude if-available -->
                <xsl:when test="$altitude!=''">
                    <altitude><xsl:value-of select="$altitude"/></altitude>
                    <xsl:if test="data[@field='ceiling']!=''">
                        <ceiling><xsl:value-of select="data[@field='ceiling']"/></ceiling>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="$elevation!=''">
                    <altitude><xsl:value-of select="$elevation"/></altitude>
                </xsl:when>
            </xsl:choose>

        </area>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- cap_area_tag -->
    <!-- These are key value pairs used for geocodes. -->
    <xsl:template match="resource[@name='cap_area_tag']">

        <geocode>
            <valueName>
                <xsl:value-of select="data[@field='tag']" />
            </valueName>
            <value>
                <xsl:value-of select="data[@field='value']" />
            </value>
        </geocode>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- cap_area_location -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="radius">
            <xsl:value-of select="data[@field='radius']" />
        </xsl:variable>
        <xsl:variable name="wkt">
            <xsl:value-of select="data[@field='wkt']/@value" />
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$radius!=''">
                <!-- Circle -->
                <xsl:variable name="lat">
                    <xsl:value-of select="data[@field='lat']" />
                </xsl:variable>
                <xsl:variable name="lon">
                    <xsl:value-of select="data[@field='lon']" />
                </xsl:variable>
                <circle>
                    <!-- Convert radius from m to km -->
                    <xsl:value-of select="concat($lat, ',', $lon, ' ', $radius * 0.001)"/>
                </circle>
            </xsl:when>
            <xsl:when test="starts-with($wkt,'&#34;POLYGON')">
                <!-- Polygon -->
                <polygon>
                    <xsl:call-template name="Polygon">
                        <xsl:with-param name="polygon">
                            <xsl:value-of select="normalize-space(substring-after($wkt,'POLYGON'))"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </polygon>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Polygon">
        <xsl:param name="polygon"/>
        <!-- Strip outer parentheses -->
        <xsl:variable name="rings" select="concat(substring-before(substring-after($polygon,'('),'))'),')')"/>
        <xsl:call-template name="Rings">
            <xsl:with-param name="rings">
                <xsl:value-of select="$rings"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Rings">
        <xsl:param name="rings"/>
        <xsl:choose>
            <xsl:when test="contains($rings,'),(')">
                <xsl:variable name="ring" select="substring-before($rings,',(')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($rings,'),'))"/>
                <xsl:call-template name="LineString">
                    <xsl:with-param name="linestring">
                        <xsl:value-of select="$ring"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>, </xsl:text>
                <xsl:call-template name="Rings">
                    <xsl:with-param name="rings">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="LineString">
                    <xsl:with-param name="linestring">
                        <xsl:value-of select="$rings"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LineString">
        <xsl:param name="linestring"/>
        <!-- Strip outer parentheses -->
        <xsl:variable name="points" select="substring-before(substring-after($linestring,'('),')')"/>
        <xsl:call-template name="Points">
            <xsl:with-param name="points">
                <xsl:value-of select="$points"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Points">
        <xsl:param name="points"/>
        <xsl:choose>
            <xsl:when test="contains($points,',')">
                <xsl:variable name="point" select="substring-before($points,',')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($points,','))"/>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point">
                        <xsl:value-of select="$point"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text> </xsl:text>
                <xsl:call-template name="Points">
                    <xsl:with-param name="points">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point">
                        <xsl:value-of select="$points"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Point">
        <xsl:param name="point"/>
        <xsl:variable name="lon" select="substring-before($point,' ')"/>
        <xsl:variable name="lat" select="substring-after($point,' ')"/>
        <xsl:value-of select="concat($lat,',',$lon)"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- OLD:
        The actual data, formatted for CAP, is stored in location tags.
        Each gis_location yields exactly one cap geometry element. Tags
        cap_circle and cap_polygon are the definitive values. For locations
        that did not have a circle or polygon, a fallback was constructed
        from whatever information was available, e.g. the bounding box (as
        a polygon) or the lat and lon or wkt point (as a zero-radius circle).
        Those are added without wasting a db lookup to see if there was a
        cap_circle. So we only use the fallback info if there was no actual
        circle or polygon. cap_circle and cap_polygon should be mutually
        exclusive, as we do not create or import a location that is both a
        polygon and a circle. The circle and polygon fallbacks are mutually
        exclusive as only one is constructed in xml_post_render.

    <xsl:template match="resource[@name='cap_area_location']//resource[@name='gis_location_tag']">
        <xsl:choose>
            <xsl:when test="./data[@field='tag']/text()='cap_circle'">
                <circle>
                    <xsl:value-of select="./data[@field='value']/text()"/>
                </circle>
            </xsl:when>
            <xsl:when test="./data[@field='tag']/text()='cap_polygon'">
                <polygon>
                    <xsl:value-of select="./data[@field='value']/text()"/>
                </polygon>
            </xsl:when>
            <xsl:when test="./data[@field='tag']/text()='cap_circle_fallback'">
                <circle>
                    <xsl:value-of select="./data[@field='value']/text()"/>
                </circle>
            </xsl:when>
            <xsl:when test="./data[@field='tag']/text()='cap_polygon_fallback'">
                <polygon>
                    <xsl:value-of select="./data[@field='value']/text()"/>
                </polygon>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
	-->

    <!-- ****************************************************************** -->
    <!-- cap_resource -->
    <xsl:template match="resource[@name='cap_resource']">
        <xsl:if test="data[@field='mime_type']!=''">
            <resource>
                <resourceDesc><xsl:value-of select="data[@field='resource_desc']"/></resourceDesc>
                <xsl:choose>
                    <xsl:when test="data[@field='mime_type']='cap'">
                        <mimeType><xsl:text>text/xml</xsl:text></mimeType>
                    </xsl:when>
                    <xsl:otherwise>
                        <mimeType><xsl:value-of select="data[@field='mime_type']"/></mimeType>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="data[@field='size']!=''">
                    <size><xsl:value-of select="data[@field='size']"/></size>
                </xsl:if>
                <xsl:if test="data[@name='size']!=''">
                    <size><xsl:value-of select="data[@name='size']"/></size>
                </xsl:if>
                <xsl:if test="data[@name='uri']!=''">
                    <uri><xsl:value-of select="data[@name='uri']"/></uri>
                </xsl:if>
                <xsl:if test="data[@name='deref_uri']!=''">
                    <derefUri><xsl:value-of select="data[@name='deref_uri']"/></derefUri>
                </xsl:if>
                <xsl:if test="data[@name='digest']!=''">
                    <digest><xsl:value-of select="data[@name='digest']"/></digest>
                </xsl:if>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Utility template used by comma-separated string templates below -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>
        <xsl:param name="last"/>

        <xsl:choose>
            <xsl:when test="$arg=''">
                <xsl:choose>
                    <xsl:when test="not($last)">
                        <xsl:choose>
                            <xsl:when test="contains($item, ' ')">
                                <xsl:text>"</xsl:text>
                                <xsl:value-of select="$item"/>
                                <xsl:text>" </xsl:text>
                             </xsl:when>
                             <xsl:otherwise>
                                <xsl:value-of select="$item"/>
                                <xsl:text> </xsl:text>
                             </xsl:otherwise>
                         </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="contains($item, ' ')">
                                <xsl:text>"</xsl:text>
                                <xsl:value-of select="$item"/>
                                <xsl:text>"</xsl:text>
                             </xsl:when>
                             <xsl:otherwise>
                                <xsl:value-of select="$item"/>
                             </xsl:otherwise>
                         </xsl:choose>
                     </xsl:otherwise>
                </xsl:choose>
            </xsl:when>

            <xsl:when test="starts-with($arg, '`')">
                <xsl:variable name="valueName">
                    <xsl:if test="contains(substring-before($item, ','), 'key:')">
                        <xsl:value-of select="normalize-space(substring-after(substring-before($item, ','), 'key:'))"/>
                    </xsl:if>
                    <xsl:if test="contains(substring-after($item, ','), 'key:')">
                        <xsl:value-of select="normalize-space(substring-after(substring-after($item, ','), 'key:'))"/>
                    </xsl:if>
                </xsl:variable>
                <xsl:variable name="value">
                    <xsl:if test="contains(substring-before($item, ','), 'value:')">
                        <xsl:value-of select="normalize-space(substring-after(substring-before($item, ','), 'value:'))"/>
                    </xsl:if>
                    <xsl:if test="contains(substring-after($item, ','), 'value:')">
                        <xsl:value-of select="normalize-space(substring-after(substring-after($item, ','), 'value:'))"/>
                    </xsl:if>
                </xsl:variable>
                <xsl:element name="{substring-after($arg, '`')}">
                    <valueName><xsl:value-of select="$valueName"/></valueName>
                    <value><xsl:value-of select="$value"/></value>
                </xsl:element>
            </xsl:when>

            <xsl:otherwise>
                <xsl:element name="{$arg}">
                    <xsl:value-of select="$item"/>
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- split a comma separated string into repeated nodes
         for example "one, two, three" as string param and
         "nodeName" as node-name param will result in:
             <nodeName>one</nodeName>
             <nodeName>two</nodeName>
             <nodeName>three</nodeName>

         @param string: the comma-separated string
         @param node-name: the name of the node
    -->
    <xsl:template name="split-into-nodes">
        <xsl:param name="string"/>
        <xsl:param name="node-name"/>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$string"/></xsl:with-param>
            <xsl:with-param name="arg"><xsl:value-of select="$node-name"/></xsl:with-param>
            <xsl:with-param name="listsep">,</xsl:with-param>
        </xsl:call-template>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- make comma separated string space delimited enclosing
         items with space in them in double-quotes.

         @param string: the comma-separated string
    -->
    <xsl:template name="make-space-delimited">
        <xsl:param name="string"/>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list">
                <xsl:value-of select="$string"/>
            </xsl:with-param>
            <xsl:with-param name="listsep">,</xsl:with-param>
            <xsl:with-param name="arg"> </xsl:with-param>  <!-- Not used -->
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- add timezone to iso timestamp

         @param time: the iso string without timezone
    -->
    <xsl:template name="add-timezone">
        <xsl:param name="time"/>

        <xsl:value-of select="$time"/>
        <!-- our time is in UTC so we just append +00:00 -->
        <xsl:text>+00:00</xsl:text>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- convert a key-value pair field to <valueName> <value> pairs

         @param string: key-value pairs of form {key1:value1},{key2:value2},...
         @param arg: the name of the node to enclose these pairs in
    -->
    <xsl:template name="key-value-pairs">
        <xsl:param name="string"/>
        <xsl:param name="arg"/>

        <xsl:call-template name="key-value-processor">
            <xsl:with-param name="key-value-col">
                <xsl:value-of select="$string"/>
            </xsl:with-param>
            <xsl:with-param name="key-value-start-sep">{</xsl:with-param>
            <xsl:with-param name="key-value-end-sep">}</xsl:with-param>
            <xsl:with-param name="arg">
                <xsl:text>`</xsl:text>
                <xsl:value-of select="$arg"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- process key-value-collections

        @param key-value-col: key-value pairs of form {key1:value1},{key2:value2},...
        @param key-value-start-sep: The start separator for the key-value collection
        @param key-value-end-sep: The ending separator for the key-value collection
        @param arg: argument to be passed on to the "resource" template
                    to allow differentiation
    -->
    <xsl:template name="key-value-processor">
        <xsl:param name="key-value-col"/>
        <xsl:param name="key-value-start-sep"/>
        <xsl:param name="key-value-end-sep"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <xsl:when test="contains($key-value-col, $key-value-start-sep) and contains($key-value-col, $key-value-end-sep)">
                <xsl:variable name="kvpairs">
                    <xsl:value-of select="substring-before(substring-after($key-value-col, $key-value-start-sep), $key-value-end-sep)"/>
                </xsl:variable>
                <xsl:variable name="remaining-kv-pairs">
                    <xsl:value-of select="substring-after($key-value-col, $kvpairs)"/>
                </xsl:variable>
                <xsl:call-template name="resource">
                    <xsl:with-param name="item" select="normalize-space($kvpairs)"/>
                    <xsl:with-param name="arg" select="$arg"/>
                </xsl:call-template>
                <xsl:call-template name="key-value-processor">
                    <xsl:with-param name="key-value-col" select="$remaining-kv-pairs"/>
                    <xsl:with-param name="key-value-start-sep" select="$key-value-start-sep"/>
                    <xsl:with-param name="key-value-end-sep" select="$key-value-end-sep"/>
                    <xsl:with-param name="arg" select="$arg"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
