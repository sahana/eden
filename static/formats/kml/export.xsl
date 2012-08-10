<xsl:stylesheet version="1.0"
  xmlns="http://www.opengis.net/kml/2.2"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************

         KML Export Templates for S3XRC

         Copyright (c) 2010-11 Sahana Software Foundation

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

    <xsl:param name="name"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <xsl:apply-templates select="s3xml"/>
            </Document>
        </kml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="s3xml">
        <Folder>
            <name>Sahana Eden Locations</name>
            <xsl:choose>
                <xsl:when test="$name='inv_item'">
                    <!-- Inventory Items don't have an FK to Locations direct, so we need to process separately -->
                    <xsl:apply-templates select=".//resource[@name='inv_inv_item']"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Process Locations (inc the resources which FK directly to a location) -->
                    <xsl:apply-templates select=".//resource[@name='gis_location']"/>
                </xsl:otherwise>
            </xsl:choose>
        </Folder>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Start with Locations -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="uid" select="./@uuid"/>
        <xsl:choose>
            <xsl:when test="//reference[@resource='gis_location' and @uuid=$uid]">
                <!-- If the Location is an FK, then process the template for the primary resource -->
                <xsl:for-each select="//reference[@resource='gis_location' and @uuid=$uid]">
                    <xsl:if test="not(../@name='gis_location')">
                        <xsl:apply-templates select=".."/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <!-- Just export the raw Location -->
                <Style>
                    <xsl:attribute name="id"><xsl:value-of select="@uuid"/></xsl:attribute>
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <styleUrl>#<xsl:value-of select="@uuid"/></styleUrl>
                    <description><xsl:value-of select="@url"/></description>
                    <Point>
                        <coordinates>
                            <xsl:value-of select="data[@field='lon']"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="data[@field='lat']"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:otherwise>
        </xsl:choose>
        <!--<xsl:value-of select="$uid"/>-->
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hospitals -->
    <xsl:template match="resource[@name='hms_hospital']">
        <xsl:if test="./reference[@field='location_id']">
            <!-- Skip records without LatLon -->
            <xsl:if test="./reference[@field='location_id']/@lon != 'null'">
            <Style id="hospital">
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <styleUrl>#hospital</styleUrl>
                    <!-- <description><xsl:value-of select="@url"/></description> -->
                    <description>
                        &lt;table&gt;
                            &lt;tr&gt;
                                &lt;td&gt;EMS Status: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='ems_status']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Facility Status: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='facility_status']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Clinical Status: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='clinical_status']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Beds total: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='total_beds']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Beds available: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='available_beds']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Details: &lt;/td&gt;
                                &lt;td&gt;&lt;a href=<xsl:value-of select="@url"/>&gt;<xsl:value-of select="@url"/>&lt;/a&gt;&lt;/td&gt;
                            &lt;/tr&gt;
                        &lt;/table&gt;
                        <xsl:if test="./resource[@name='hms_shortage']/data[@field='status']/@value='1' or ./resource[@name='hms_shortage']/data[@field='status']/@value='2'">
                            &lt;ul&gt;
                            <xsl:apply-templates select="./resource[@name='hms_shortage']"/>
                            &lt;/ul&gt;
                        </xsl:if>
                        <xsl:if test="./resource[@name='hms_ctc_capability']/data[@field='ctc']/@value='True'">
                            &lt;h4&gt;CTC Information:&lt;/h4&gt;
                            &lt;ul&gt;
                            <xsl:apply-templates select="./resource[@name='hms_ctc_capability']"/>
                            &lt;/ul&gt;
                        </xsl:if>
                    </description>
                    <Point>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <xsl:template match="resource[@name='hms_shortage']">
        <xsl:if test="./data[@field='status']/@value='1' or ./data[@field='status']/@value='2'">
            &lt;li&gt;Shortage [<xsl:value-of select="./data[@field='priority']/text()"/>/<xsl:value-of select="./data[@field='impact']/text()"/>/<xsl:value-of select="./data[@field='type']/text()"/>]: <xsl:value-of select="./data[@field='description']/text()"/>&lt;/li&gt;
        </xsl:if>
    </xsl:template>

    <xsl:template match="resource[@name='hms_ctc_capability']">
        &lt;li&gt;Current number of patients: <xsl:value-of select="./data[@field='number_of_patients']/text()"/>&lt;/li&gt;
        &lt;li&gt;New cases in the past 24h: <xsl:value-of select="./data[@field='cases_24']/text()"/>&lt;/li&gt;
        &lt;li&gt;Deaths in the past 24h: <xsl:value-of select="./data[@field='deaths_24']/text()"/>&lt;/li&gt;
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Human Resources (Staff/Volunteers) -->
    <!-- @ToDo: Add Skills -->
    <xsl:template match="resource[@name='hrm_human_resource']">
        <xsl:if test="./reference[@field='location_id']">
            <!-- Skip records without LatLon -->
            <xsl:if test="./reference[@field='location_id']/@lon != 'null'">
                <Style><xsl:attribute name="id"><xsl:value-of select="reference[@field='location_id']/@uuid"/></xsl:attribute>
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="reference[@field='person_id']/text()"/></name>
                    <styleUrl>#<xsl:value-of select="reference[@field='location_id']/@uuid"/></styleUrl>
                    <description>
                        <xsl:text>&lt;table&gt;&lt;tr&gt;</xsl:text>
                        <xsl:text>&lt;td&gt;&lt;a href=</xsl:text>
                        <xsl:choose>
                            <xsl:when test="data[@field='type']/@value=1">
                                    <xsl:value-of select="concat(substring-before(@url, 'human_resource'), 'staff', substring-after(@url, 'human_resource'))"/>
                            </xsl:when>
                            <xsl:when test="data[@field='type']/@value=2">
                                    <xsl:value-of select="concat(substring-before(@url, 'human_resource'), 'volunteer', substring-after(@url, 'human_resource'))"/>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:text>&gt;</xsl:text>
                        <xsl:value-of select="reference[@field='person_id']/text()"/>
                        <xsl:text>&lt;/a&gt;&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                        <xsl:value-of select="reference[@field='site_id']/text()"/>
                        <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                        <xsl:value-of select="data[@field='job_title']"/>
                        <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:text>&lt;/table&gt;</xsl:text>
                    </description>

                    <Point>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Inventory Items -->
    <xsl:template match="resource[@name='inv_inv_item']">
        <xsl:variable name="item_name" select="./reference[@field='item_id']/text()"/>
        <xsl:variable name="item_quantity" select="./data[@field='quantity']/text()"/>
        <xsl:variable name="item_url" select="@url"/>
        <xsl:variable name="site_id" select="./reference[@field='site_id']/@uuid"/>
        <xsl:for-each select="//resource[@uuid=$site_id]">
            <xsl:call-template name="site">
                <xsl:with-param name="item_name" select="$item_name"/>
                <xsl:with-param name="item_quantity" select="$item_quantity"/>
                <xsl:with-param name="item_url" select="$item_url"/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Offices -->
    <xsl:template match="resource[@name='org_office']">
        <xsl:if test="./reference[@field='location_id']">
            <!-- Skip records without LatLon -->
            <xsl:if test="./reference[@field='location_id']/@lon != 'null'">
                <Style><xsl:attribute name="id"><xsl:value-of select="reference[@field='location_id']/@uuid"/></xsl:attribute>
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <styleUrl>#<xsl:value-of select="reference[@field='location_id']/@uuid"/></styleUrl>
                    <description>
                        <xsl:text>&lt;table&gt;&lt;tr&gt;</xsl:text>
                        <xsl:text>&lt;td&gt;&lt;a href=</xsl:text>
                            <xsl:value-of select="@url"/>
                        <xsl:text>&gt;</xsl:text>
                        <xsl:value-of select="data[@field='name']"/>
                        <xsl:text>&lt;/a&gt;&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:if test="./data[@field='phone1'] != 'null'">
                            <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                            <xsl:value-of select="data[@field='phone1']"/>
                            <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        </xsl:if>
                        <!-- Inventory Items (Stock Position Report) -->
                        <xsl:for-each select="./resource[@name='inv_inv_item']">
                            <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                            <xsl:value-of select="./data[@field='quantity']/text()"/><xsl:text> </xsl:text><xsl:value-of select="./reference[@field='item_id']/text()"/>
                            <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        </xsl:for-each>
                        <xsl:text>&lt;/table&gt;</xsl:text>
                    </description>

                    <Point>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Warehouses -->
    <xsl:template match="resource[@name='inv_warehouse']">
        <xsl:if test="./reference[@field='location_id']">
            <!-- Skip records without LatLon -->
            <xsl:if test="./reference[@field='location_id']/@lon != 'null'">
                <Style><xsl:attribute name="id"><xsl:value-of select="reference[@field='location_id']/@uuid"/></xsl:attribute>
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <styleUrl>#<xsl:value-of select="reference[@field='location_id']/@uuid"/></styleUrl>
                    <description>
                        <xsl:text>&lt;table&gt;&lt;tr&gt;</xsl:text>
                        <xsl:text>&lt;td&gt;&lt;a href=</xsl:text>
                            <xsl:value-of select="@url"/>
                        <xsl:text>&gt;</xsl:text>
                        <xsl:value-of select="data[@field='name']"/>
                        <xsl:text>&lt;/a&gt;&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:if test="./data[@field='phone1'] != 'null'">
                            <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                            <xsl:value-of select="data[@field='phone1']"/>
                            <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        </xsl:if>
                        <!-- Inventory Items (Stock Position Report) -->
                        <xsl:for-each select="./resource[@name='inv_inv_item']">
                            <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                            <xsl:value-of select="./data[@field='quantity']/text()"/><xsl:text> </xsl:text><xsl:value-of select="./reference[@field='item_id']/text()"/>
                            <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        </xsl:for-each>
                        <xsl:text>&lt;/table&gt;</xsl:text>
                    </description>

                    <Point>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Sites (called by inv_inv_item) -->
    <xsl:template name="site">
        <xsl:param name="item_name"/>
        <xsl:param name="item_quantity"/>
        <xsl:param name="item_url"/>
        <xsl:if test="./reference[@field='location_id']">
            <!-- Skip records without LatLon -->
            <xsl:if test="./reference[@field='location_id']/@lon != 'null'">
                <Style><xsl:attribute name="id"><xsl:value-of select="reference[@field='location_id']/@uuid"/></xsl:attribute>
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="$item_name"/></name>
                    <styleUrl>#<xsl:value-of select="reference[@field='location_id']/@uuid"/></styleUrl>
                    <description>
                        <xsl:text>&lt;table&gt;&lt;tr&gt;</xsl:text>
                        <xsl:text>&lt;td&gt;&lt;a href=</xsl:text>
                        <xsl:value-of select="$item_url"/>
                        <xsl:text>&gt;</xsl:text>
                        <xsl:value-of select="$item_name"/>
                        <xsl:text>&lt;/a&gt;&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                        <xsl:text>Quantity: </xsl:text><xsl:value-of select="$item_quantity"/>
                        <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                        <xsl:text>Inventory: </xsl:text><xsl:value-of select="data[@field='name']"/>
                        <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                        <xsl:if test="./data[@field='phone1']">
                            <!-- Offices/Warehouses -->
                            <xsl:if test="./data[@field='phone1'] != 'null'">
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:text>Contact: </xsl:text><xsl:value-of select="data[@field='phone1']"/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:if>
                        </xsl:if>
                        <xsl:if test="./data[@field='phone']">
                            <!-- Shelters -->
                            <xsl:if test="./data[@field='phone'] != 'null'">
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:text>Contact: </xsl:text><xsl:value-of select="data[@field='phone']"/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:if>
                        </xsl:if>
                        <xsl:if test="./data[@field='phone_exchange']">
                            <!-- Hospitals -->
                            <xsl:if test="./data[@field='phone_exchange'] != 'null'">
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:text>Contact: </xsl:text><xsl:value-of select="data[@field='phone_exchange']"/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:if>
                        </xsl:if>
                        <xsl:text>&lt;/table&gt;</xsl:text>
                    </description>

                    <Point>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Everything without a specific section -->
    <xsl:template match="resource">
        <xsl:if test="./reference[@field='location_id']">
            <!-- Skip records without LatLon -->
            <xsl:if test="./reference[@field='location_id']/@lon != 'null'">
                <Style><xsl:attribute name="id"><xsl:value-of select="reference[@field='location_id']/@uuid"/></xsl:attribute>
                    <IconStyle>
                        <Icon>
                            <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <styleUrl>#<xsl:value-of select="reference[@field='location_id']/@uuid"/></styleUrl>
                    <description><xsl:value-of select="@url"/></description>
                    <Point>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:if>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
