<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Case Appointment Type - CSV Import Stylesheet

         CSV column..................Format..........Content

         Name........................string..........Type Name
         Active......................string..........is active
                                                     true|false
         Mandatory for Children......string..........is mandatory for children
                                                     true|false
         Mandatory for Adolescents...string..........is mandatory for adolescents
                                                     true|false
         Mandatory for Adults........string..........is mandatory for adults
                                                     true|false
         Presence required...........string..........requires personal presence
                                                     true|false
         Comments....................string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="dvr_case_appointment_type">

            <!-- Basic details -->

            <data field="name">
                <xsl:value-of select="col[@field='Name']"/>
            </data>

            <!-- Is active -->

            <xsl:variable name="is_active" select="col[@field='Active']/text()"/>
            <data field="active">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_active='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <!-- Mandatory for age groups -->

            <xsl:variable name="mandatory_children" select="col[@field='Mandatory for Children']/text()"/>
            <data field="mandatory_children">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$mandatory_children='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <xsl:variable name="mandatory_adolescents" select="col[@field='Mandatory for Adolescents']/text()"/>
            <data field="mandatory_adolescents">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$mandatory_adolescents='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <xsl:variable name="mandatory_adults" select="col[@field='Mandatory for Adults']/text()"/>
            <data field="mandatory_adults">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$mandatory_adults='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <!-- Requires personal presence -->

            <xsl:variable name="presence_required" select="col[@field='Presence required']/text()"/>
            <data field="presence_required">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$presence_required='false'">
                            <xsl:value-of select="'false'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'true'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <!-- Comments -->

            <data field="comments">
                <xsl:value-of select="col[@field='Comments']"/>
            </data>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
