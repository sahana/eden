<?xml version="1.0"?>
<xsl:stylesheet
    xmlns="urn:oasis:names:tc:emergency:EDXL:DE:1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:rm="urn:oasis:names:tc:emergency:EDXL:RM:1.0:msg"
    xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3"
    xmlns:xnl="urn:oasis:names:tc:cqi:xnl:3"
    xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
    xmlns:s3="urn:sahana:eden:s3">

    <!-- ****************************************************************** -->
    <!-- UID/TUID for organisations -->
    <xsl:template name="OrganisationUID">
        <xsl:param name="contact"/>
        <xsl:variable name="uuid" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/@xnl:Identifier"/>
        <xsl:variable name="name" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text()"/>
        <xsl:choose>
            <xsl:when test="$uuid">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$uuid"/>
                </xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($uuid, $name)"/>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- UID/TUID for persons -->
    <xsl:template name="PersonUID">
        <xsl:param name="contact"/>
        <xsl:variable name="uuid" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/@xnl:Identifier"/>
        <xsl:variable name="first_name" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text()"/>
        <xsl:variable name="last_name" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text()"/>
        <xsl:variable name="email" select="$contact/rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text()"/>
        <xsl:choose>
            <xsl:when test="$uuid">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$uuid"/>
                </xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($uuid, $first_name, $last_name, $email)"/>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- UID/TUID for human resources -->
    <xsl:template name="HumanResourceUID">
        <xsl:param name="contact"/>
        <xsl:variable name="uuid" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/@xpil:ID"/>
        <xsl:variable name="first_name" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text()"/>
        <xsl:variable name="last_name" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text()"/>
        <xsl:variable name="org_name" select="$contact/rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text()"/>
        <xsl:variable name="email" select="$contact/rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text()"/>
        <xsl:choose>
            <xsl:when test="$uuid">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$uuid"/>
                </xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($uuid, $first_name, $last_name, $org_name, $email)"/>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- TODO: UID/TUID for sites -->

    <!-- ****************************************************************** -->
    <!-- TODO: UID/TUID for locations -->

    <!-- ****************************************************************** -->
    <!-- UID/TUID for supply_items -->
    <xsl:template name="SupplyItemUID">
        <xsl:choose>
            <xsl:when test="@s3:uuid">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="@s3:uuid"/>
                </xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <!-- TODO: context-dependend position() not reliable -->
                <xsl:attribute name="tuid">
                    <xsl:value-of select="generate-id(.)"/>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- TODO: UID/TUID for supply_item_packs -->

    <!-- ****************************************************************** -->
    <!-- TODO: UID/TUID for skills -->

</xsl:stylesheet>
