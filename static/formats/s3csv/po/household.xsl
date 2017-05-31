<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Outreach Household - CSV Import Stylesheet

         CSV fields:
         Area....................po_area.name
         Country.................gis_location.L0 Name or ISO2 country code
         L1......................gis_location.L1
         L2......................gis_location.L2
         L3......................gis_location.L3
         L4......................gis_location.L4
         L5......................gis_location.L5
         Address.................gis_location.addr_street
         Postcode................gis_location.addr_postcode
         Lat.....................gis_location.lat
         Lon.....................gis_location.lon
         Follow Up...............po_household.followup (Y|N)
         Date Visited............po_household.date_visited (YYYY-MM-DD)
         Phone...................pr_contact.value
         Mobile Phone............pr_contact.value
         Email...................pr_contact.value
         Sticker.................po_household_dwelling.sticker
         Emotional Needs.........po_emotional_need.name
         Practical Needs.........po_practical_need.name
         Dwelling Type...........po_household_dwelling.dwelling_type
                                 Unit|House|Apartment|Supervised House|Other
         Type of Use.............po_household_dwelling.type_of_use
                                 Owner-occupied|Renting|Boarding|Other
         Stage of Repair.........po_household_dwelling.repair_status
                                 waiting|rebuild|completed|not required|other
         Main Language...........po_household_social.language
                                 English|Maori|Samoan|Hindi|Chinese|French|German|Tonga
                                 or ISO 639-2 Alpha-2/3 language code
         Community Connections...po_household_social.community (free text)

         Follow-up required......po_household_followup.followup_required (free text)
         Follow-up Date..........po_household_followup.followup_date (YYYY-MM-DD)
         Follow-up made..........po_household_followup.followup (free text)
         Follow-up completed.....po_household_followup.completed (Y|N)
         Evaluation..............po_household_followup.evaluation
                                 better|same|worse
         Follow-up Comments......po_household_followup.comments (free text)
         Referral Agency.........org_organisation.name
         Referral Date...........po_household_organisation.date
         Referral Comments.......po_household_organisation.comments
         Comments................po_household.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->
    <xsl:variable name="Country">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Country</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="Lat">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lat</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Lon">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lon</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Postcode">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Postcode</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->

    <!-- Areas -->
    <xsl:key name="areas" match="row" use="col[@field='Area']"/>

    <!-- Lx -->
    <xsl:key name="L1" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'])"/>
    <xsl:key name="L2" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'])"/>
    <xsl:key name="L3" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'])"/>
    <xsl:key name="L4" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'])"/>

    <xsl:key name="L5" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'], '/',
                         col[@field='L5'])"/>

    <!-- Referral Agencies -->
    <xsl:key name="agencies" match="row" use="col[@field='Referral Agency']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Areas -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('areas', col[@field='Area'])[1])]">
                <xsl:call-template name="Area"/>
            </xsl:for-each>

            <!-- Referral Agencies -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('agencies', col[@field='Referral Agency'])[1])]">
                <xsl:call-template name="ReferralAgency"/>
            </xsl:for-each>

            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L1',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1']))[1])]">
                <xsl:call-template name="L1"/>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L2',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2']))[1])]">
                <xsl:call-template name="L2"/>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L3',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3']))[1])]">
                <xsl:call-template name="L3"/>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L4',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4']))[1])]">
                <xsl:call-template name="L4"/>
            </xsl:for-each>

            <!-- L5 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L5',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4'], '/',
                                                                          col[@field='L5']))[1])]">
                <xsl:call-template name="L5"/>
            </xsl:for-each>

            <!-- Households -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="address" select="col[@field='Address']/text()"/>
        <xsl:variable name="AreaName" select="col[@field='Area']/text()"/>

        <xsl:if test="$AreaName!=''">
            <resource name="po_household">

                <!-- Link to area -->
                <reference field="area_id" resource="po_area">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('AREA:', $AreaName)"/>
                    </xsl:attribute>
                </reference>

                <!-- Location -->
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('HOUSEHOLD:', $AreaName, '|', $postcode, '|', $address)"/>
                    </xsl:attribute>
                </reference>

                <!-- Comments -->
                <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
                <xsl:if test="$Comments!=''">
                    <data field='comments'>
                        <xsl:value-of select="$Comments"/>
                    </data>
                </xsl:if>

                <!-- Follow up -->
                <xsl:variable name="FollowUp">
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                            <xsl:value-of select="col[@field='Follow Up']/text()"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="starts-with($FollowUp, 'Y') or starts-with($FollowUp, 'T')">
                        <data field="followup" value="true">True</data>
                    </xsl:when>
                    <xsl:when test="starts-with($FollowUp, 'N') or starts-with($FollowUp, 'F')">
                        <data field="followup" value="false">False</data>
                    </xsl:when>
                </xsl:choose>

                <!-- Date Visited -->
                <xsl:variable name="DateVisited" select="col[@field='Date Visited']/text()"/>
                <xsl:if test="$DateVisited!=''">
                    <data field="date_visited">
                        <xsl:value-of select="$DateVisited"/>
                    </data>
                </xsl:if>

                <!-- Contact Information -->
                <xsl:variable name="Phone" select="col[@field='Phone']/text()"/>
                <xsl:if test="$Phone!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">HOME_PHONE</data>
                        <data field="value">
                            <xsl:value-of select="$Phone"/>
                        </data>
                    </resource>
                </xsl:if>
                <xsl:variable name="MobilePhone" select="col[@field='Mobile Phone']/text()"/>
                <xsl:if test="$MobilePhone!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">SMS</data>
                        <data field="value">
                            <xsl:value-of select="$MobilePhone"/>
                        </data>
                    </resource>
                </xsl:if>
                <xsl:variable name="Email" select="col[@field='Email']/text()"/>
                <xsl:if test="$Email!=''">
                    <resource name="pr_contact">
                        <data field="contact_method">EMAIL</data>
                        <data field="value">
                            <xsl:value-of select="$Email"/>
                        </data>
                    </resource>
                </xsl:if>

                <!-- Emotional Needs -->
                <xsl:variable name="EmotionalNeeds" select="col[@field='Emotional Needs']/text()"/>
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list" select="$EmotionalNeeds"/>
                    <xsl:with-param name="arg">emotional_need</xsl:with-param>
                </xsl:call-template>

                <!-- Practical Needs -->
                <xsl:variable name="PracticalNeeds" select="col[@field='Practical Needs']/text()"/>
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list" select="$PracticalNeeds"/>
                    <xsl:with-param name="arg">practical_need</xsl:with-param>
                </xsl:call-template>

                <!-- Social Information -->
                <xsl:variable name="MainLanguage" select="col[@field='Main Language']/text()"/>
                <xsl:variable name="Community" select="col[@field='Community Connections']/text()"/>
                <xsl:if test="$MainLanguage!='' or $Community!=''">
                    <resource name="po_household_social">
                        <xsl:if test="$MainLanguage!=''">
                            <data field="language">
                                <xsl:choose>
                                    <xsl:when test="$MainLanguage='English'">en</xsl:when>
                                    <xsl:when test="$MainLanguage='Maori'">mi</xsl:when>
                                    <xsl:when test="$MainLanguage='Samoan'">sm</xsl:when>
                                    <xsl:when test="$MainLanguage='Hindi'">hi</xsl:when>
                                    <xsl:when test="$MainLanguage='Chinese'">zh</xsl:when>
                                    <xsl:when test="$MainLanguage='French'">fr</xsl:when>
                                    <xsl:when test="$MainLanguage='German'">de</xsl:when>
                                    <xsl:when test="$MainLanguage='Tonga'">to</xsl:when>
                                    <xsl:when test="string-length($MainLanguage)=2 or string-length($MainLanguage)=3">
                                        <!-- Assume Language Code -->
                                        <xsl:value-of select="$MainLanguage"/>
                                    </xsl:when>
                                </xsl:choose>
                            </data>
                        </xsl:if>
                        <xsl:if test="$Community!=''">
                            <data field="community">
                                <xsl:value-of select="$Community"/>
                            </data>
                        </xsl:if>
                    </resource>
                </xsl:if>

                <!-- Dwelling Information -->
                <xsl:variable name="Sticker" select="col[@field='Sticker']/text()"/>
                <xsl:variable name="DwellingType" select="col[@field='Dwelling Type']/text()"/>
                <xsl:variable name="TypeOfUse" select="col[@field='Type of Use']/text()"/>
                <xsl:variable name="RepairStatus"  select="col[@field='Stage of Repair']/text()"/>
                <xsl:if test="$Sticker!='' or $DwellingType!='' or $TypeOfUse!='' or $RepairStatus!=''">
                    <resource name="po_household_dwelling">
                        <xsl:if test="$Sticker!=''">
                            <data field="sticker">
                                <xsl:choose>
                                    <xsl:when test="$Sticker='White'">W</xsl:when>
                                    <xsl:when test="$Sticker='Yellow'">Y</xsl:when>
                                    <xsl:when test="$Sticker='Red'">R</xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="$Sticker"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </data>
                        </xsl:if>
                        <xsl:if test="$DwellingType!=''">
                            <data field="dwelling_type">
                                <xsl:choose>
                                    <xsl:when test="$DwellingType='Unit'">U</xsl:when>
                                    <xsl:when test="$DwellingType='House'">H</xsl:when>
                                    <xsl:when test="$DwellingType='Apartment'">A</xsl:when>
                                    <xsl:when test="$DwellingType='Supervised House'">S</xsl:when>
                                    <xsl:otherwise>O</xsl:otherwise>
                                </xsl:choose>
                            </data>
                        </xsl:if>
                        <xsl:if test="$TypeOfUse!=''">
                            <data field="type_of_use">
                                <xsl:choose>
                                    <xsl:when test="$TypeOfUse='Owner-occupied'">S</xsl:when>
                                    <xsl:when test="$TypeOfUse='Renting'">R</xsl:when>
                                    <xsl:when test="$TypeOfUse='Boarding'">B</xsl:when>
                                    <xsl:otherwise>O</xsl:otherwise>
                                </xsl:choose>
                            </data>
                        </xsl:if>
                        <xsl:if test="$RepairStatus!=''">
                            <data field="repair_status">
                                <xsl:choose>
                                    <xsl:when test="$RepairStatus='waiting'">W</xsl:when>
                                    <xsl:when test="$RepairStatus='rebuild'">R</xsl:when>
                                    <xsl:when test="$RepairStatus='completed'">C</xsl:when>
                                    <xsl:when test="$RepairStatus='not required'">N</xsl:when>
                                    <xsl:otherwise>O</xsl:otherwise>
                                </xsl:choose>
                            </data>
                        </xsl:if>
                    </resource>
                </xsl:if>

                <!-- Follow-up Details -->
                <xsl:variable name="FollowupRequired" select="col[@field='Follow-up required']/text()"/>
                <xsl:variable name="FollowupDate" select="col[@field='Follow-up Date']/text()"/>
                <xsl:variable name="FollowupMade" select="col[@field='Follow-up made']/text()"/>
                <xsl:variable name="FollowupCompleted">
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                            <xsl:value-of select="col[@field='Follow-up completed']/text()"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="Evaluation" select="col[@field='Evaluation']/text()"/>
                <xsl:variable name="FollowupComments" select="col[@field='Follow-up Comments']/text()"/>

                <xsl:if test="$FollowupRequired!='' or
                              $FollowupDate!='' or
                              $FollowupMade!='' or
                              $FollowupCompleted!='' or
                              $Evaluation!='' or
                              $FollowupComments!=''">
                    <resource name="po_household_followup">
                        <xsl:if test="$FollowupRequired!=''">
                            <data field="folloup_required">
                                <xsl:value-of select="$FollowupRequired"/>
                            </data>
                        </xsl:if>
                        <xsl:if test="$FollowupDate!=''">
                            <data field="followup_date">
                                <xsl:value-of select="$FollowupDate"/>
                            </data>
                        </xsl:if>
                        <xsl:if test="$FollowupMade!=''">
                            <data field="followup">
                                <xsl:value-of select="$FollowupMade"/>
                            </data>
                        </xsl:if>
                        <xsl:choose>
                            <xsl:when test="starts-with($FollowupCompleted, 'Y') or starts-with($FollowupCompleted, 'T')">
                                <data field="completed" value="true">True</data>
                            </xsl:when>
                            <xsl:when test="starts-with($FollowupCompleted, 'N') or starts-with($FollowupCompleted, 'F')">
                                <data field="completed" value="false">False</data>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="$Evaluation!=''">
                            <data field="evaluation">
                                <xsl:choose>
                                    <xsl:when test="$Evaluation='better'">B</xsl:when>
                                    <xsl:when test="$Evaluation='same'">S</xsl:when>
                                    <xsl:when test="$Evaluation='worse'">W</xsl:when>
                                </xsl:choose>
                            </data>
                        </xsl:if>
                        <xsl:if test="$FollowupComments!=''">
                            <data field="comments">
                                <xsl:value-of select="$FollowupComments"/>
                            </data>
                        </xsl:if>
                    </resource>
                </xsl:if>

                <!-- Referral -->
                <xsl:variable name="ReferralAgency" select="col[@field='Referral Agency']/text()"/>
                <xsl:variable name="ReferralDate" select="col[@field='Referral Date']/text()"/>
                <xsl:variable name="ReferralComments" select="col[@field='Referral Comments']/text()"/>

                <xsl:if test="$ReferralAgency!=''">
                    <resource name="po_organisation_household">
                        <reference field="organisation_id" resource="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('ORG:', $ReferralAgency)"/>
                            </xsl:attribute>
                        </reference>
                        <xsl:if test="$ReferralDate!=''">
                            <data field="date">
                                <xsl:value-of select="$ReferralDate"/>
                            </data>
                        </xsl:if>
                        <xsl:if test="$ReferralComments!=''">
                            <data field="comments">
                                <xsl:value-of select="$ReferralComments"/>
                            </data>
                        </xsl:if>
                    </resource>
                </xsl:if>

            </resource>
            <xsl:call-template name="Locations"/>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Area">

        <xsl:variable name="AreaName" select="col[@field='Area']/text()"/>

        <xsl:if test="$AreaName!=''">
            <resource name="po_area">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('AREA:', $AreaName)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$AreaName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>

            <!-- Emotional Needs -->
            <xsl:when test="$arg='emotional_need'">
                <resource name="po_household_emotional_need">
                    <reference field="emotional_need_id" resource="po_emotional_need">
                        <resource name="po_emotional_need">
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>

            <!-- Practical Needs -->
            <xsl:when test="$arg='practical_need'">
                <resource name="po_household_practical_need">
                    <reference field="practical_need_id" resource="po_practical_need">
                        <resource name="po_practical_need">
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>

        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:if test="col[@field='L1']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <!-- Parent to Country -->
                <xsl:if test="$countrycode!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:if test="col[@field='L2']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:if test="col[@field='L3']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:if test="col[@field='L4']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L5">
        <xsl:if test="col[@field='L5']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>
            <xsl:variable name="l5" select="col[@field='L5']/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l5"/></data>
                <data field="level"><xsl:text>L5</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L4']!=''">
                        <!-- Parent to L4 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="lon">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lon"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="address" select="col[@field='Address']/text()"/>
        <xsl:variable name="area" select="col[@field='Area']/text()"/>

        <!-- Country Code = UUID of the L0 Location -->
        <xsl:variable name="countrycode">
            <xsl:choose>
                <xsl:when test="string-length($l0)!=2">
                    <xsl:call-template name="countryname2iso">
                        <xsl:with-param name="country">
                            <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                           <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <xsl:variable name="l1id" select="concat('L1/', $countrycode, '/', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>

        <!-- Office Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('HOUSEHOLD:', $area, '|', $postcode, '|', $address)"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l5!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l5id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l4id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l3id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l2id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l1id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:otherwise>
            </xsl:choose>
            <data field="name">
                <xsl:value-of select="concat('Household:', $countrycode, ',', $postcode, ',', $address)"/>
            </data>
            <data field="addr_street"><xsl:value-of select="$address"/></data>
            <data field="addr_postcode"><xsl:value-of select="$postcode"/></data>
            <data field="lat"><xsl:value-of select="$lat"/></data>
            <data field="lon"><xsl:value-of select="$lon"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ReferralAgency">

        <xsl:variable name="OrgName" select="col[@field='Referral Agency']/text()"/>

        <xsl:if test="$OrgName!=''">
            <xsl:variable name="tuid" select="concat('ORG:', $OrgName)"/>

            <!-- Organisation Record -->
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
                <!-- Context Reference -->
                <resource name="po_referral_organisation">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$tuid"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </resource>

        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
