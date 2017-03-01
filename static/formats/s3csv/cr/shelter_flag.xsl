<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CR Shelter Flag - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Flag Name
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

        <xsl:variable name="Name" select="col[@field='Name']"/>
        <xsl:if test="$Name!=''">
            <resource name="cr_shelter_flag">

                <!-- Flag Name -->
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>

                <!-- Comments -->
                <data field="comments">
                    <xsl:value-of select="col[@field='Comments']"/>
                </data>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
