<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************

         CAP Export Templates for S3XRC

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
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="/s3xml">
        <xsl:apply-templates select="./resource[@name='cap_alert']"/>
    </xsl:template>

    <!-- util -->
    <xsl:include href="../xml/commons.xsl"/>

    <!-- Utility template used by comma-seperated string templates below -->
    <xsl:template name="resource" match="//*" xmlns = "urn:oasis:names:tc:emergency:cap:1.2">
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
                <xsl:element name="{substring-after($arg, '`')}">
                    <valueName><xsl:value-of select="substring-before($item, ':')"/></valueName>
                    <value><xsl:value-of select="substring-after($item, ':')"/></value>
                </xsl:element>
            </xsl:when>

            <xsl:otherwise>
                <xsl:element name="{$arg}">
                    <xsl:value-of select="$item"/>
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
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

    <!-- make comma separated string space delimited enclosing
         items with space in them in double-quotes.

         @param string: the comma-separated string
    -->
    <xsl:template name="make-space-delimited">
        <xsl:param name="string"/>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$string"/></xsl:with-param>
            <xsl:with-param name="listsep">,</xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <!-- convert a key-value pair field to <valueName> <value> pairs

         @param string: the comma-separated string
         @param arg: the name of the node to enclose these pairs in
    -->
    <xsl:template name="key-value-pairs">
        <xsl:param name="string"/>
        <xsl:param name="arg"/>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$string"/></xsl:with-param>
            <xsl:with-param name="listsep">,</xsl:with-param>
            <xsl:with-param name="arg">
                <xsl:text>`</xsl:text>
                <xsl:value-of select="$arg"/>
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <!-- add timezone to iso timestamp

         @param time: the iso string without timezone
    -->
    <xsl:template name="add-timezone">
        <xsl:param name="time"/>

        <xsl:value-of select="$time"/>
        <!-- our time is in UTC so we just append +00:00 -->
        <xsl:text>+00:00</xsl:text>
    </xsl:template>

    <!-- *********************** cap_alert ******************************** -->
    <xsl:template match="resource[@name='cap_alert']">
        <alert xmlns = "urn:oasis:names:tc:emergency:cap:1.2">
            <identifier><xsl:value-of select="data[@field='identifier']"/></identifier>
            <sender><xsl:value-of select="data[@field='sender']"/></sender>

            <sent>
                <xsl:call-template name="add-timezone">
                    <xsl:with-param name="time">
                        <xsl:choose>
                            <xsl:when test="data[@field='sent']!=''">
                                <xsl:value-of select="data[@field='sent']"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="@created_on"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:with-param>
                </xsl:call-template>
            </sent>

            <status><xsl:value-of select="data[@field='status']"/></status>
            <msgType><xsl:value-of select="data[@field='msg_type']"/></msgType>

            <xsl:if test="data[@field='source']!=''">
                <source><xsl:value-of select="data[@field='source']"/></source>
            </xsl:if>

            <scope><xsl:value-of select="data[@field='scope']"/></scope>

            <xsl:if test="data[@field='scope']='Restricted'">
                <restriction><xsl:value-of select="data[@field='restriction']"/></restriction>
            </xsl:if>

            <xsl:if test="data[@field='addresses']">
                <addresses>
                    <xsl:call-template name="make-space-delimited">
                        <xsl:with-param name="string"><xsl:value-of select="data[@field='addresses']"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </addresses>
            </xsl:if>

            <xsl:if test="data[@field='codes']">
                <xsl:call-template name="key-value-pairs">
                    <xsl:with-param name="string"><xsl:value-of select="data[@field='codes']"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">code</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="data[@field='note']!=''">
                <note><xsl:value-of select="data[@field='note']"/></note>
            </xsl:if>

            <xsl:if test="data[@field='incidents']">
                <incidents>
                    <xsl:call-template name="make-space-delimited">
                        <xsl:with-param name="string"><xsl:value-of select="data[@field='incidents']"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </incidents>
            </xsl:if>

            <xsl:apply-templates select="resource[@name='cap_info']"/>
        </alert>
    </xsl:template>

    <!-- *********************** cap_info ********************************* -->
    <xsl:template match="resource[@name='cap_info']">
        <info xmlns = "urn:oasis:names:tc:emergency:cap:1.2">
            <xsl:if test="data[@field='language']!=''">
                <language><xsl:value-of select="data[@field='language']"/></language>
            </xsl:if>

            <xsl:if test="data[@field='category']">
                <xsl:call-template name="split-into-nodes">
                    <xsl:with-param name="string"><xsl:value-of select="data[@field='category']"/>
                    </xsl:with-param>
                    <xsl:with-param name="node-name">category</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <event><xsl:value-of select="data[@field='event']"/></event>

            <xsl:if test="data[@field='response_type']">
                <xsl:call-template name="split-into-nodes">
                    <xsl:with-param name="string"><xsl:value-of select="data[@field='response_type']"/>
                    </xsl:with-param>
                    <xsl:with-param name="node-name">responseType</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <urgency><xsl:value-of select="data[@field='urgency']"/></urgency>
            <severity><xsl:value-of select="data[@field='severity']"/></severity>
            <certainty><xsl:value-of select="data[@field='certainty']"/></certainty>

            <xsl:if test="data[@field='audience']!=''">
                <audience><xsl:value-of select="data[@field='audience']"/></audience>
            </xsl:if>

            <xsl:if test="data[@field='event_code']">
                <xsl:call-template name="key-value-pairs">
                    <xsl:with-param name="string"><xsl:value-of select="data[@field='event_code']"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">eventCode</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="data[@field='effective']">
                <effective>
                    <xsl:call-template name="add-timezone">
                        <xsl:with-param name="time">
                            <xsl:value-of select="data[@field='effective']"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </effective>
            </xsl:if>

            <xsl:if test="data[@field='onset']">
                <onset>
                    <xsl:call-template name="add-timezone">
                        <xsl:with-param name="time">
                            <xsl:value-of select="data[@field='onset']"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </onset>
            </xsl:if>

            <xsl:if test="data[@field='expires']">
                <expires>
                    <xsl:call-template name="add-timezone">
                        <xsl:with-param name="time">
                            <xsl:value-of select="data[@field='expires']"/>
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
                <web><xsl:value-of select="data[@field='web']"/></web>
            </xsl:if>

            <xsl:if test="data[@field='contact']!=''">
                <contact><xsl:value-of select="data[@field='contact']"/></contact>
            </xsl:if>

            <xsl:if test="data[@field='parameter']">
                <xsl:call-template name="key-value-pairs">
                    <xsl:with-param name="string"><xsl:value-of select="data[@field='parameter']"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">parameter</xsl:with-param>
                </xsl:call-template>
            </xsl:if>
            <!--
            <xsl:if test="../resource[@name='cap_info_resource']/info_id = @uuid">
                <xsl:apply-templates select="resource[@name='cap_info_resource']"/>
                <xsl:apply-templates select="resource[@name='cap_info_area']"/>
            </xsl:if> -->
        </info>
    </xsl:template>

    <!-- *********************** cap_info_area **************************** -->
    <xsl:template match="resource[@name='cap_info_area']">
        <area>
            <areaDesc><xsl:value-of select="data[@field='area_desc']"/></areaDesc>
            <xsl:if test="data[@name='polygon']!=''">
                <polygon><xsl:value-of select="data[@name='polygon']"/></polygon>
            </xsl:if>
            <xsl:if test="data[@field='circle']!=''">
                <circle><xsl:value-of select="data[@field='circle']"/></circle>
            </xsl:if>
            <xsl:if test="data[@field='geocode']!=''">
                <geocode><xsl:value-of select="data[@field='geocode']"/></geocode>
            </xsl:if>
            <xsl:if test="data[@name='altitude']!=''">
                <altitude><xsl:value-of select="data[@name='altitude']"/></altitude>
            </xsl:if>
            <xsl:if test="data[@name='ceiling']!=''">
                <ceiling><xsl:value-of select="data[@name='ceiling']"/></ceiling>
            </xsl:if>
        </area>
    </xsl:template>

    <!-- *********************** cap_info_resource ************************ -->
    <xsl:template match="resource[@name='cap_info_resource']">
        <resource>
            <resourceDesc><xsl:value-of select="data[@field='resource_desc']"/></resourceDesc>
            <mimeType><xsl:value-of select="data[@field='mime_type']"/></mimeType>
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
    </xsl:template>
</xsl:stylesheet>
