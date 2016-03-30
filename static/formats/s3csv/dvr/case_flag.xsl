<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         DVR Case Flag - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Type Name
         External.............string..........Flag indicates that person is
                                              currently external
                                              true|false
         Not Transferable.....string..........Cases with this flag are not transferable
                                              true|false
         Comments.............string..........Comments

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
        <resource name="dvr_case_flag">

            <data field="name">
                <xsl:value-of select="col[@field='Name']"/>
            </data>

            <xsl:variable name="is_external" select="col[@field='External']/text()"/>
            <data field="is_external">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_external='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <xsl:variable name="is_not_transferable" select="col[@field='Not Transferable']/text()"/>
            <data field="is_not_transferable">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$is_not_transferable='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <data field="comments">
                <xsl:value-of select="col[@field='Comments']"/>
            </data>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
