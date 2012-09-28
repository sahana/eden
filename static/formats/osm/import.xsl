<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:osm="http://openstreetmap.org/osm/0.6">

    <!-- Sahana Eden XSLT Import Templates

        Transformation of
            OpenStreetMap Points of Interest
        into
            Sahana Eden Records:
                Airports, Hospitals, Offices, Seaports, Shelters, and their Locations

        Large files can give memory errors, so best to reduce the file first to just the bounding box &/or tag type of interest:
        e.g. (replace single hyphens with double-hyphens)
        osmosis -read-xml haiti.osm -way-key-value keyValueList="amenity.hospital" -used-node -write-xml haiti_hospital.osm
    -->

    <xsl:output method="xml"/>

    <xsl:param name="name"/>

    <xsl:key name="nodes" match="node" use="@id" />

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="./osm"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="osm">
        <s3xml>
            <xsl:choose>
                <!-- Airports -->
                <xsl:when test="$name='airport'">
                    <xsl:apply-templates select="node[./tag[@k='aeroway' and @v='aerodrome']]|way[./tag[@k='aeroway' and @v='aerodrome']]"/>
                </xsl:when>
                <!-- Hospitals -->
                <!-- @ToDo: Pharmacies (http://wiki.openstreetmap.org/wiki/Tag:amenity%3Dpharmacy) -->
                <xsl:when test="$name='hospital'">
                    <xsl:apply-templates select="node[./tag[@k='amenity' and @v='hospital']]|way[./tag[@k='amenity' and @v='hospital']]|node[./tag[@k='amenity' and @v='clinic']]|way[./tag[@k='amenity' and @v='clinic']]"/>
                </xsl:when>
                <!-- Offices -->
                <xsl:when test="$name='office'">
                    <xsl:apply-templates select="node[./tag[@k='office' and @v='ngo']]|way[./tag[@k='office' and @v='ngo']]"/>
                </xsl:when>
                <!-- Churches & Schools -->
                <xsl:when test="$name='facility'">
                    <xsl:apply-templates select="node[./tag[@k='amenity' and @v='place_of_worship']]|way[./tag[@k='amenity' and @v='place_of_worship']]|node[./tag[@k='amenity' and @v='school']]|way[./tag[@k='amenity' and @v='school']]"/>
                </xsl:when>
                <!-- Sea Ports -->
                <xsl:when test="$name='seaport'">
                    <xsl:apply-templates select="node[./tag[@k='harbour' and @v='yes']]|way[./tag[@k='harbour' and @v='yes']]"/>
                </xsl:when>
                <!-- Shelters -->
                <xsl:when test="$name='shelter'">
                    <xsl:apply-templates select="node[./tag[@k='refugee' and @v='yes']]|way[./tag[@k='refugee' and @v='yes']]"/>
                </xsl:when>
                <!-- Default: Locations -->
                <xsl:otherwise>
                    <xsl:apply-templates select="node|way"/>
                    <!-- @ToDo: Handle Relations (minority case): lookup all linked ways, & hence nodes, create WKT & pull in as polygon or multipolygon -->
                </xsl:otherwise>

            </xsl:choose>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="node|way">
        <xsl:choose>
            <xsl:when test="$name='airport'">
                <xsl:call-template name="airport"/>
            </xsl:when>
            <xsl:when test="$name='hospital'">
                <xsl:call-template name="hospital"/>
            </xsl:when>
            <xsl:when test="$name='office'">
                <xsl:call-template name="office"/>
            </xsl:when>
            <xsl:when test="$name='seaport'">
                <xsl:call-template name="seaport"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="location"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="airport">
        <resource name="transport_airport">

            <xsl:attribute name="modified_on">
                <xsl:call-template name="datetime">
                    <xsl:with-param name="datetime" select="@timestamp"/>
                </xsl:call-template>
            </xsl:attribute>

            <data field="name">
                <xsl:value-of select="./tag[@k='name']/@v"/>
            </data>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="facility">
        <resource name="org_facility">

            <xsl:attribute name="modified_on">
                <xsl:call-template name="datetime">
                    <xsl:with-param name="datetime" select="@timestamp"/>
                </xsl:call-template>
            </xsl:attribute>

            <data field="name">
                <xsl:value-of select="./tag[@k='name']/@v"/>
            </data>
            
            <reference field="facility_type_id" resource="org_facility_type">
                <data field="name">
                    <xsl:choose>
                        <xsl:when test="./tag[@v='place_of_worship']">
                            <xsl:text>Church</xsl:text>
                        </xsl:when>
                        <xsl:when test="./tag[@v='school']">
                            <xsl:text>School</xsl:text>
                        </xsl:when>
                    </xsl:choose>
                </data>
            </reference>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="hospital">
        <resource name="hms_hospital">

            <xsl:attribute name="modified_on">
                <xsl:call-template name="datetime">
                    <xsl:with-param name="datetime" select="@timestamp"/>
                </xsl:call-template>
            </xsl:attribute>

            <xsl:if test="./tag[@k='paho:id']">
                <data field="gov_uuid">
                    <xsl:value-of select="concat('urn:paho:id:', ./tag[@k='paho:id']/@v)"/>
                </data>
            </xsl:if>

            <!-- Main Record -->
            <data field="name">
                <xsl:choose>
                    <xsl:when test="./tag[@k='name']">
                        <xsl:value-of select="./tag[@k='name']/@v"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat('Facility #', @id)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <!--
            Can add Hospital-specific tags here
                http://wiki.openstreetmap.org/wiki/Tag:amenity%3Dhospital
                    <tag k="paho:damage" v="Damaged"/>
                    <tag k="paho:damage" v="Severe"/>
            -->

            <xsl:for-each select="./tag[starts-with(@k, 'name:')][1]">
            
                <data field="aka1">
                    <xsl:value-of select="@v"/>
                </data>
            </xsl:for-each>

            <!-- health_facility:type and health_facility:bed -->
            <data field="facility_type">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="./tag[@k='health_facility:type']">
                            <xsl:for-each select="./tag[@k='health_facility:type'][1]">
                                <xsl:choose>
                                    <xsl:when test="@v='hospital'">1</xsl:when>
                                    <xsl:when test="@v='field_hospital'">2</xsl:when>
                                    <xsl:when test="@v='specialized_hospital'">3</xsl:when>
                                    <xsl:when test="@v='health_center'">
                                        <xsl:choose>
                                            <xsl:when test="../tag[@k='health_facility:bed' and @v='yes']">12</xsl:when>
                                            <xsl:when test="../tag[@k='health_facility:bed' and @v='no']">13</xsl:when>
                                            <xsl:otherwise>11</xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:when>
                                    <xsl:when test="@v='dispensary'">21</xsl:when>
                                    <xsl:otherwise>98</xsl:otherwise>
                                </xsl:choose>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:otherwise>1</xsl:otherwise> <!-- can we simply assume that? otherwise should be 99 -->
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <xsl:for-each select="./tag[@k='bed_capacity' or @k='building:beds'][1]">
                <resource name="hms_bed_capacity">
                    <data field="bed_type" value="6"/>
                    <data field="beds_baseline" value="@v"/>
                </resource>
            </xsl:for-each>

            <xsl:for-each select="./tag[@k='emergency'][1]">
                <xsl:if test="@v='yes'">
                    <resource name="hms_services">
                        <data field="emsd" value="True"/>
                    </resource>
                </xsl:if>
            </xsl:for-each>

            <xsl:if test="./tag[@k='contact:phone' or @k='phone' or @k='phone_number' or @k='telephone']">
                <data field="phone_exchange">
                    <xsl:call-template name="phone_exchange"/>
                </data>
            </xsl:if>

            <xsl:if test="./tag[@k='emergency_phone' or @k='emergency_department_phone']">
                <data field="phone_business">
                    <xsl:call-template name="phone_business"/>
                </data>
            </xsl:if>

            <xsl:if test="./tag[@k='emergency_phone' or @k='emergency_department_phone']">
                <data field="phone_emergency">
                    <xsl:call-template name="phone_emergency"/>
                </data>
            </xsl:if>

            <xsl:for-each select="./tag[@k='contact:website' or @k='website' or @k='url'][1]">
                <data field="website">
                    <xsl:value-of select="@v"/>
                </data>
            </xsl:for-each>

            <xsl:for-each select="./tag[@k='picture'][1]">
                <resource name="hms_image">
                    <data field="type" value="1"/>
                    <!-- Use either url (link the image) or image (upload the image) -->
                <!--<data field="url">
                        <xsl:value-of select="@v"/>
                    </data>-->
                    <data field="image">
                        <xsl:attribute name="filename">
                            <xsl:value-of select="@v"/>
                        </xsl:attribute>
                        <xsl:attribute name="url">
                            <xsl:value-of select="@v"/>
                        </xsl:attribute>
                    </data>
                </resource>
            </xsl:for-each>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="office">
        <resource name="org_office">

            <xsl:attribute name="modified_on">
                <xsl:call-template name="datetime">
                    <xsl:with-param name="datetime" select="@timestamp"/>
                </xsl:call-template>
            </xsl:attribute>

            <data field="name">
                <xsl:value-of select="./tag[@k='name']/@v"/>
            </data>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="seaport">
        <resource name="transport_seaport">

            <xsl:attribute name="modified_on">
                <xsl:call-template name="datetime">
                    <xsl:with-param name="datetime" select="@timestamp"/>
                </xsl:call-template>
            </xsl:attribute>

            <data field="name">
                <xsl:value-of select="./tag[@k='name']/@v"/>
            </data>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="shelter">
        <resource name="cr_shelter">

            <xsl:attribute name="modified_on">
                <xsl:call-template name="datetime">
                    <xsl:with-param name="datetime" select="@timestamp"/>
                </xsl:call-template>
            </xsl:attribute>

            <data field="name">
                <xsl:value-of select="./tag[@k='name']/@v"/>
            </data>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <resource name="gis_location">

            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('urn:osm:id:', @id)"/>
            </xsl:attribute>

            <xsl:attribute name="modified_on">
                <xsl:call-template name="datetime">
                    <xsl:with-param name="datetime" select="@timestamp"/>
                </xsl:call-template>
            </xsl:attribute>

            <!-- Tag this record with the OSM ID -->
            <resource name="gis_location_tag">
                <data field="tag">
                    <xsl:text>openstreetmap</xsl:text>
                </data>
                <data field="value">
                    <xsl:value-of select="@id"/>
                </data>
            </resource>

            <!-- @ToDo: Is there a way of combining housenumber with street
                        name that will be recognizable across countries?
                        What does the Universal Postal Union prescribe?
                        http://www.upu.int/en/activities/addressing/postal-addressing-systems-in-member-countries.html
                        http://www.columbia.edu/kermit/postal.html
                 @ToDo: Is there a better way to conditionally include
                        punctuation?
            -->
            <xsl:if test="./tag[@k='addr:housenumber' or @k='addr:street' or @k='addr:city']">
                <data field="addr_street">
                    <xsl:for-each select="./tag[@k='addr:housenumber'][1]">
                        <xsl:value-of select="@v"/>
                        <xsl:text> </xsl:text>
                    </xsl:for-each>
                    <xsl:for-each select="./tag[@k='addr:street'][1]">
                        <xsl:value-of select="@v"/>
                        <xsl:text>, </xsl:text>
                    </xsl:for-each>
                    <xsl:for-each select="./tag[@k='addr:city'][1]">
                        <xsl:value-of select="@v"/>
                    </xsl:for-each>
                </data>
            </xsl:if>

            <xsl:for-each select="./tag[@k='addr:postcode'][1]">
                <data field="addr_postcode">
                    <xsl:value-of select="@v"/>
                </data>
            </xsl:for-each>

            <!-- @ToDo: Handle Source
            e.g.
            <tag k="source" v="US Census Bureau"/> -->


            <xsl:choose>

                <!-- Admin Boundaries: http://wiki.openstreetmap.org/wiki/Tag:boundary%3Dadministrative -->
                <!-- @ToDo: How to handle the variability of levels per-country? -->
                <xsl:when test="./tag[@k='boundary'] and ./tag[@v='administrative']">
                    <xsl:choose>
                        <xsl:when test="./tag[@k='admin_level'] and ./tag[@v='2']">
                            <data field="level">
                                <xsl:text>L0</xsl:text>
                            </data>
                        </xsl:when>
                        <!-- 4 is the right level for Haiti -->
                        <xsl:when test="./tag[@k='admin_level'] and ./tag[@v='4']">
                            <data field="level">
                                <xsl:text>L1</xsl:text>
                            </data>
                        </xsl:when>
                        <!-- 8 is the right level for Haiti -->
                        <xsl:when test="./tag[@k='admin_level'] and ./tag[@v='8']">
                            <data field="level">
                                <xsl:text>L2</xsl:text>
                            </data>
                        </xsl:when>
                    </xsl:choose>
                </xsl:when>

                <xsl:when test="./tag[@k='place'] and ./tag[@v='town']">
                    <data field="level">
                        <xsl:text>L3</xsl:text>
                    </data>
                </xsl:when>

                <xsl:when test="./tag[@k='place'] and ./tag[@v='village']">
                    <data field="level">
                        <xsl:text>L4</xsl:text>
                    </data>
                </xsl:when>

            </xsl:choose>

            <data field="name">
                <xsl:choose>
                    <xsl:when test="./tag[@k='name']">
                        <xsl:value-of select="./tag[@k='name']/@v"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat('OSM #', @id)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <xsl:choose>
                <xsl:when test="local-name()='node'">
                    <data field="gis_feature_type" value="1">Point</data>
                    <data field="lat">
                        <xsl:value-of select="@lat"/>
                    </data>
                    <data field="lon">
                        <xsl:value-of select="@lon"/>
                    </data>
                </xsl:when>
                <xsl:when test="local-name()='way'">
                    <!-- Note that we assume a closed way here. The onvalidation routine will try an open way (LINESTRING) if the POLYGON import fails -->
                    <data field="gis_feature_type" value="3">Polygon</data>
                    <data field="wkt">
                        <xsl:text>POLYGON((</xsl:text>
                        <xsl:for-each select="./nd">
                            <xsl:variable name="id" select="@ref"/>
                            <xsl:for-each select="key('nodes', $id)[1]">
                                <xsl:value-of select="concat(@lon, ' ', @lat)"/>
                            </xsl:for-each>
                            <xsl:if test="following-sibling::nd">
                                <xsl:text>,</xsl:text>
                            </xsl:if>
                        </xsl:for-each>
                        <xsl:text>))</xsl:text>
                    </data>
                </xsl:when>
            </xsl:choose>

            <!-- @ToDo: Support Is-In
            <data field="parent">
                <xsl:value-of select=""/>
            </data>
            -->

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="datetime">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, 'T'),' ',substring-before(substring-after($datetime, 'T'), 'Z'))"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="phone_exchange">
        <xsl:for-each select="./tag[@k='contact:phone' or @k='phone' or @k='phone_number' or @k='telephone']">
            <xsl:if test="position() != 1">
                <xsl:text>; </xsl:text>
            </xsl:if>
            <xsl:value-of select="@v"/>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="phone_business">
        <xsl:for-each select="./tag[@k='sahana:phone_business']">
            <xsl:if test="position() != 1">
                <xsl:text>; </xsl:text>
            </xsl:if>
            <xsl:value-of select="@v"/>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="phone_emergency">
        <xsl:for-each select="./tag[@k='emergency_phone' or @k='emergency_department_phone']">
            <xsl:if test="position() != 1">
                <xsl:text>; </xsl:text>
            </xsl:if>
            <xsl:value-of select="@v"/>
        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>
