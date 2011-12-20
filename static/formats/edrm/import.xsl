<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:rm="urn:oasis:names:tc:emergency:EDXL:RM:1.0:msg"
    xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3"
    xmlns:xnl="urn:oasis:names:tc:cqi:xnl:3"
    xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
    xmlns:s3="urn:sahana:eden:s3">

    <!-- **********************************************************************

         EDXL-RM Import Templates

         Version 0.1 / 2011-08-01 / Dominic König <dominic[at]aidiq[dot]com>

         Copyright (c) 2010 Sahana Software Foundation

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
    <xsl:output method="xml"/>

    <xsl:include href="ciq.xsl"/>
    <xsl:include href="uid.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Keys -->
    <xsl:key name="human_resources"
             match="rm:ContactInformation"
             use="concat(rm:AdditionalContactInformation/xpil:PartyName/@xpil:ID,
                         rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text(),
                         rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text(),
                         rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text(),
                         rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text())"/>

    <xsl:key name="persons"
             match="rm:ContactInformation"
             use="concat(rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/@xnl:Identifier,
                         rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text(),
                         rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text(),
                         rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text())"/>

    <xsl:key name="organisations"
             match="rm:ContactInformation"
             use="concat(rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/@xnl:Identifier,
                         rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text())"/>

    <!-- TODO: offices -->
    <!-- TODO: locations -->
    <!-- TODO: supply_items -->
    <!-- TODO: supply_item_packs -->
    <!-- TODO: hrm_skill -->

    <!-- ****************************************************************** -->
    <!-- Root template -->
    <xsl:template match="/">
        <s3xml>
            <!-- req_req -->
            <xsl:apply-templates select="//rm:RequestResource|//rm:ResponseToRequestResource"/>

            <!-- hrm_human_resource -->
            <xsl:for-each select="//rm:ContactInformation[
                            generate-id(.)=generate-id(key('human_resources',
                            concat(rm:AdditionalContactInformation/xpil:PartyName/@xpil:ID,
                                   rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text(),
                                   rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text(),
                                   rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text(),
                                   rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text())
                            )[1])]">
                <xsl:for-each select="key('human_resources',
                                      concat(rm:AdditionalContactInformation/xpil:PartyName/@xpil:ID,
                                             rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text(),
                                             rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text(),
                                             rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text(),
                                             rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text())
                                      )">
                    <xsl:if test="position() = 1">
                        <xsl:apply-templates select="." mode="human_resource"/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:for-each>

            <!-- pr_person -->
            <xsl:for-each select="//rm:ContactInformation[
                            generate-id(.)=generate-id(key('persons',
                            concat(rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/@xnl:Identifier,
                                   rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text(),
                                   rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text(),
                                   rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text())
                            )[1])]">
                <xsl:for-each select="key('persons',
                                      concat(rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/@xnl:Identifier,
                                             rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text(),
                                             rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text(),
                                             rm:AdditionalContactInformation/xpil:ElectronicAddressIdentifiers/xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL']/text())
                                      )">
                    <xsl:if test="position() = 1">
                        <xsl:apply-templates select="." mode="person"/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:for-each>

            <!-- org_organisation -->
            <xsl:for-each select="//rm:ContactInformation[
                            generate-id(.)=generate-id(key('organisations',
                            concat(rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/@xnl:Identifier,
                                   rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text())
                            )[1])]">
                <xsl:for-each select="key('organisations',
                                      concat(rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/@xnl:Identifier,
                                             rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text())
                                      )">
                    <xsl:if test="position() = 1">
                        <xsl:apply-templates select="." mode="organisation"/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:for-each>

            <!-- TODO: org_office -->

            <!-- TODO: gis_location -->

            <!-- TODO: supply_item -->

            <!-- TODO: supply_item_pack -->

            <!-- TODO: hrm_skill -->

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- REQUEST                                                            -->
    <!-- ****************************************************************** -->
    <xsl:template match="rm:RequestResource|rm:ResponseToRequestResource">
        <resource name="req_req">

            <!-- EDXL-RM encodes all request data per resource item,
                 while Eden does it per request, so we take those data
                 from the first Resource instance in the input document -->
            <xsl:variable name="first" select="rm:ResourceInformation[1]/rm:Resource[1]"/>

            <!-- Request Identity -->
            <!-- type -->
            <xsl:call-template name="RequestType"/>
            <!-- request_number -->
            <data field="request_number"><xsl:value-of select="rm:OriginatingMessageID/text()"/></data>
            <!-- date and time_requested -->
            <xsl:call-template name="DateTime">
                <xsl:with-param name="datetime" select="rm:SentDateTime/text()"/>
                <xsl:with-param name="date" select="string('date')"/>
                <xsl:with-param name="time" select="string('time_requested')"/>
            </xsl:call-template>

            <!-- Request Data -->
            <!-- priority -->
            <xsl:apply-templates
                select="$first/rm:Keyword[rm:ValueListURN/text()='urn:sahana:eden:request:priority']"/>
            <!-- purpose -->
            <xsl:apply-templates
                select="$first/rm:AssignmentInformation[1]/rm:AnticipatedFunction[last()]">
                <xsl:with-param name="field">purpose</xsl:with-param>
            </xsl:apply-templates>

            <!-- date_required and time_required -->
            <xsl:apply-templates
                select="$first/rm:ScheduleInformation[rm:ScheduleType/text()='RequestedArrival']/rm:DateTime"/>
            <!-- date_required_until and time_required_until -->
            <xsl:apply-templates
                select="$first/rm:ScheduleInformation[rm:ScheduleType/text()='EstimatedReturnDeparture']/rm:DateTime"/>
            <!-- transport_req and security_req -->
            <xsl:apply-templates
                select="$first/rm:AssignmentInformation[1]/rm:Restrictions[last()]"/>
            <!-- commit_status, transit_status, fulfil_status -->
            <xsl:apply-templates
                select="$first//rm:DeploymentStatus[last()]"/>
            <!-- cancel -->
            <xsl:apply-templates
                select="$first/rm:ResponseInformation[1]"/>
            <!-- TODO: comments (not implemented in export either) -->

            <!-- Contact Information -->
            <!-- requester_id -->
            <xsl:apply-templates
                select="rm:ContactInformation[rm:ContactRole/text()='Requester'][1]"
                mode="reference">
                <xsl:with-param name="field" select="string('requester_id')"/>
            </xsl:apply-templates>
            <!-- assigned_to_id -->
            <xsl:apply-templates
                select="rm:ContactInformation[rm:ContactRole/text()='RespondingOrg'][1]"
                mode="reference">
                <xsl:with-param name="field" select="string('assigned_to_id')"/>
            </xsl:apply-templates>
            <!-- approved_by_id -->
            <xsl:apply-templates
                select="rm:ContactInformation[rm:ContactRole/text()='Approver'][1]"
                mode="reference">
                <xsl:with-param name="field" select="string('approved_by_id')"/>
            </xsl:apply-templates>
            <!-- request_for_id -->
            <xsl:apply-templates
                select="rm:ContactInformation[rm:ContactDescription/text()='Deliver to' or
                                              rm:ContactDescription/text()='Report to'][1]"
                mode="reference">
                <xsl:with-param name="field" select="string('request_for_id')"/>
            </xsl:apply-templates>
            <!-- recv_by_id -->
            <xsl:apply-templates
                select="rm:ContactInformation[rm:ContactDescription/text()='Delivered to' or
                                              rm:ContactDescription/text()='Reported to'][1]"
                mode="reference">
                <xsl:with-param name="field" select="string('recv_by_id')"/>
            </xsl:apply-templates>

            <xsl:apply-templates select="rm:ResourceInformation"/>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- REQUEST DETAILS                                                    -->
    <!-- ****************************************************************** -->
    <!-- Map the resource name to a request type -->
    <xsl:template name="RequestType">
        <xsl:variable name="name" select="rm:ResourceInformation[1]/rm:Resource[1]/rm:Name"/>
        <!-- This mapping must match the mapping in the export stylesheet -->
        <xsl:variable name="type">
            <xsl:choose>
                <xsl:when test="$name='Volunteer'">3</xsl:when>
                <xsl:otherwise>1</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <data field="type">
            <xsl:attribute name="value">
                <xsl:value-of select="$type"/>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Request status -->
    <xsl:template match="rm:DeploymentStatus[rm:ValueListURN/text()='urn:sahana:eden:request:status']">
        <xsl:variable name="commit_status">
            <xsl:value-of select="normalize-space(substring-after(rm:Value[starts-with(./text(), 'Committed:')][last()]/text(), ':'))"/>
        </xsl:variable>
        <xsl:variable name="fulfil_status">
            <xsl:value-of select="normalize-space(substring-after(rm:Value[starts-with(./text(), 'Fulfilled:')][last()]/text(), ':'))"/>
        </xsl:variable>
        <xsl:variable name="transit_status">
            <xsl:value-of select="normalize-space(substring-after(rm:Value[starts-with(./text(), 'InTransit:')][last()]/text(), ':'))"/>
        </xsl:variable>
        <data field="commit_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$commit_status='Full'">2</xsl:when>
                    <xsl:when test="$commit_status='Partial'">1</xsl:when>
                    <xsl:otherwise>0</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>
        <data field="fulfil_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$fulfil_status='Full'">2</xsl:when>
                    <xsl:when test="$fulfil_status='Partial'">1</xsl:when>
                    <xsl:otherwise>0</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>
        <data field="transit_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$transit_status='Full'">2</xsl:when>
                    <xsl:when test="$transit_status='Partial'">1</xsl:when>
                    <xsl:otherwise>0</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ResponseInformation to cancel -->
    <xsl:template match="rm:ResponseInformation">
        <data field="cancel">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="normalize-space(rm:ResponseType/text())='Cancel'">true</xsl:when>
                    <xsl:otherwise>false</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Keyword to priority -->
    <xsl:template match="rm:Keyword[rm:ValueListURN/text()='urn:sahana:eden:request:priority']">
        <xsl:variable name="priority" select="rm:Value[last()]/text()"/>
        <data field="priority">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$priority='High'">3</xsl:when>
                    <xsl:when test="$priority='Medium'">2</xsl:when>
                    <xsl:otherwise>1</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Restrictions (transportation required, security required) -->
    <xsl:template match="rm:Restrictions">
        <xsl:variable name="transport" select="normalize-space(substring-after(./text(), 'TransportationRequired:'))" />
        <xsl:variable name="security" select="normalize-space(substring-after(./text(), 'SecurityRequired:'))" />
        <data field="transport_req">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="starts-with($transport, 'yes')">true</xsl:when>
                    <xsl:otherwise>false</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>
        <data field="security_req">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="starts-with($security, 'yes')">true</xsl:when>
                    <xsl:otherwise>false</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Schedule datetimes -->
    <xsl:template match="rm:ScheduleInformation/rm:DateTime">
        <xsl:variable name="suffix">
            <xsl:choose>
                <xsl:when test="../rm:ScheduleType/text()='ActualReceived'">recv</xsl:when>
                <xsl:when test="../rm:ScheduleType/text()='EstimatedReturnDeparture'">required_until</xsl:when>
                <xsl:otherwise>required</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:call-template name="DateTime">
            <xsl:with-param name="datetime" select="./text()"/>
            <xsl:with-param name="date" select="concat('date_', $suffix)"/>
            <xsl:with-param name="time" select="concat('time_', $suffix)"/>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Human resource references -->
    <xsl:template match="rm:ContactInformation" mode="reference">
        <xsl:param name="field"/>
        <reference resource="hrm_human_resource">
            <xsl:attribute name="field">
                <xsl:value-of select="$field"/>
            </xsl:attribute>
            <xsl:call-template name="HumanResourceUID">
                <xsl:with-param name="contact" select="."/>
            </xsl:call-template>
        </reference>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- RESOURCE                                                           -->
    <!-- ****************************************************************** -->
    <xsl:template match="rm:ResourceInformation">
        <xsl:apply-templates select="rm:Resource"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Resource -->
    <xsl:template match="rm:Resource">
        <xsl:variable name="type" select="rm:Name/text()"/>
        <xsl:choose>
            <xsl:when test="$type='Volunteer'">
                <xsl:call-template name="Skill"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Item"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Skill -->
    <xsl:template name="Skill">
        <xsl:variable name="uuid" select="../rm:ResourceInfoElementID/text()"/>
        <resource name="req_req_skill">
            <xsl:if test="$uuid">
                <xsl:attribute name="uuid"><xsl:value-of select="$uuid"/></xsl:attribute>
            </xsl:if>
            <!-- Task -->
            <xsl:apply-templates select="rm:AssignmentInformation/rm:AnticipatedFunction">
                <xsl:with-param name="field">task</xsl:with-param>
            </xsl:apply-templates>
            <!-- Quantity -->
            <xsl:apply-templates select="rm:AssignmentInformation/rm:Quantity"/>
            <!-- Quantity committed, fulfilled, in transit -->
            <xsl:apply-templates select="rm:ResourceStatus" mode="quantity"/>
            <!-- Comments -->
            <xsl:apply-templates select="rm:Description"/>
            <!-- Skills reference -->
            <xsl:apply-templates select="rm:Keyword[rm:ValueListURN/text()='urn:sahana:eden:skills']"
                                 mode="reference"/>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Item -->
    <xsl:template name="Item">
        <xsl:variable name="uuid" select="../rm:ResourceInfoElementID/text()"/>
        <resource name="req_req_item">
            <xsl:if test="$uuid">
                <xsl:attribute name="uuid"><xsl:value-of select="$uuid"/></xsl:attribute>
            </xsl:if>
            <!-- Quantity -->
            <xsl:apply-templates select="rm:AssignmentInformation/rm:Quantity"/>
            <!-- Pack value and Currency -->
            <xsl:apply-templates select="rm:AssignmentInformation/rm:PriceQuote"/>
            <!-- Quantity committed, fulfilled, in transit -->
            <xsl:apply-templates select="rm:ResourceStatus" mode="quantity"/>
            <!-- Comments -->
            <xsl:apply-templates select="rm:Description"/>
            <!-- Supply Item -->
            <xsl:apply-templates select="rm:TypeStructure[rm:ValueListURN/text()='urn:sahana:eden:request:items']"
                                 mode="reference"/>
            <!-- TODO: Supply Item Pack -->
<!--             <reference field="item_pack_id" resource="supply_item_pack" uuid="urn:uuid:ca9ad484-7b0d-4ec3-8d11-dee29367f5e0">kit</reference> -->
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- RESOURCE DETAILS                                                   -->
    <!-- ****************************************************************** -->
    <!-- AnticipatedFunction to purpose or task -->
    <xsl:template match="rm:AnticipatedFunction">
        <xsl:param name="field"/>
        <xsl:if test="normalize-space(./text())">
            <data>
                <xsl:attribute name="field">
                    <xsl:value-of select="$field"/>
                </xsl:attribute>
                <xsl:value-of select="normalize-space(text())"/>
            </data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Description to comments -->
    <xsl:template match="rm:Resource/rm:Description">
        <xsl:if test="normalize-space(./text())">
            <data field="comments"><xsl:value-of select="normalize-space(text())"/></data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- rm:Quantity to quantity -->
    <xsl:template match="rm:Quantity">
        <data field="quantity">
            <xsl:attribute name="value">
                <xsl:value-of select="rm:MeasuredQuantity/rm:Amount/text()"/>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- rm:ResourceStatus to committed/fulfilled/in-transit quantity -->
    <xsl:template match="rm:ResourceStatus" mode="quantity">
        <xsl:apply-templates select="rm:Availability[starts-with(text(), 'QuantityCommitted:')][last()]"/>
        <xsl:apply-templates select="rm:Availability[starts-with(text(), 'QuantityFulfilled:')][last()]"/>
        <xsl:apply-templates select="rm:Availability[starts-with(text(), 'QuantityInTransit:')][last()]"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- rm:Availability to committed/fulfilled/in-transit quantity -->
    <xsl:template match="rm:Availability">
        <xsl:choose>
            <xsl:when test="starts-with(text(), 'QuantityCommitted:')">
                <data field="quantity_commit">
                    <xsl:attribute name="value">
                        <xsl:value-of select="normalize-space(substring-after(text(), 'QuantityCommitted:'))"/>
                    </xsl:attribute>
                </data>
            </xsl:when>
            <xsl:when test="starts-with(text(), 'QuantityFulfilled:')">
                <data field="quantity_fulfil">
                    <xsl:attribute name="value">
                        <xsl:value-of select="normalize-space(substring-after(text(), 'QuantityFulfilled:'))"/>
                    </xsl:attribute>
                </data>
            </xsl:when>
            <xsl:when test="starts-with(text(), 'QuantityInTransit:')">
                <data field="quantity_transit">
                    <xsl:attribute name="value">
                        <xsl:value-of select="normalize-space(substring-after(text(), 'QuantityInTransit:'))"/>
                    </xsl:attribute>
                </data>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- TypeStructure to supply_item references -->
    <xsl:template match="rm:TypeStructure[rm:ValueListURN='urn:sahana:eden:request:items']"
                  mode="reference">
        <xsl:apply-templates select="rm:Value[1]" mode="reference"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- rm:Value to supply_item reference -->
    <xsl:template match="rm:Value[../rm:ValueListURN='urn:sahana:eden:request:items']"
                  mode="reference">
        <reference field="item_id" resource="supply_item">
            <xsl:call-template name="SupplyItemUID"/>
        </reference>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Keyword to hrm_skill references -->
    <xsl:template match="rm:Keyword[rm:ValueListURN='urn:sahana:eden:skills']"
                  mode="reference">
        <!-- TODO: this maybe wrong: can only have either uuids or tuids? -->
<!--         <xsl:apply-templates select="rm:Value[not(@s3:uuid)][1]" mode="reference"/> -->
        <xsl:apply-templates select="rm:Value[@s3:uuid][1]" mode="reference"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- rm:Value to hrm_skill reference -->
    <xsl:template match="rm:Value[../rm:ValueListURN='urn:sahana:eden:skills' and @s3:uuid]"
                  mode="reference">
        <xsl:choose>
            <xsl:when test="preceding-sibling::rm:Value[@s3:uuid]">
                <xsl:value-of select="concat('&quot;', @s3:uuid, '&quot;')"/>
                <xsl:choose>
                    <xsl:when test="following-sibling::rm:Value[@s3:uuid]">,</xsl:when>
                    <xsl:otherwise>]</xsl:otherwise>
                </xsl:choose>
                <xsl:apply-templates select="following-sibling::rm:Value[@s3:uuid][1]"
                                     mode="reference"/>
            </xsl:when>
            <xsl:otherwise>
                <reference field="skill_id" resource="hrm_skill">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="concat('[&quot;', @s3:uuid, '&quot;')"/>
                        <xsl:choose>
                            <xsl:when test="following-sibling::rm:Value[@s3:uuid]">,</xsl:when>
                            <xsl:otherwise>]</xsl:otherwise>
                        </xsl:choose>
                        <xsl:apply-templates select="following-sibling::rm:Value[@s3:uuid][1]"
                                             mode="reference"/>
                    </xsl:attribute>
                </reference>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- rm:Value to hrm_skill reference -->
    <xsl:template match="rm:Value[../rm:ValueListURN='urn:sahana:eden:skills' and not(@s3:uuid)]"
                  mode="reference">
        <xsl:choose>
            <xsl:when test="preceding-sibling::rm:Value[not(@s3:uuid)]">
                <xsl:value-of select="concat('&quot;', generate-id(.), '&quot;')"/>
                <xsl:choose>
                    <xsl:when test="following-sibling::rm:Value[not(@s3:uuid)]">,</xsl:when>
                    <xsl:otherwise>]</xsl:otherwise>
                </xsl:choose>
                <xsl:apply-templates select="following-sibling::rm:Value[not(@s3:uuid)][1]"
                                     mode="reference"/>
            </xsl:when>
            <xsl:otherwise>
                <reference field="skill_id" resource="hrm_skill">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('[&quot;', generate-id(.), '&quot;')"/>
                        <xsl:choose>
                            <xsl:when test="following-sibling::rm:Value[not(@s3:uuid)]">,</xsl:when>
                            <xsl:otherwise>]</xsl:otherwise>
                        </xsl:choose>
                        <xsl:apply-templates select="following-sibling::rm:Value[not(@s3:uuid)][1]"
                                             mode="reference"/>
                    </xsl:attribute>
                </reference>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Price quote to currency and pack_value -->
    <xsl:template match="rm:PriceQuote">
        <xsl:apply-templates select="rm:MeasuredQuantity"/>
    </xsl:template>

    <xsl:template match="rm:MeasuredQuantity[rm:Unit/rm:ValueListURN/text()='urn:sahana:eden:request:currency']">
        <xsl:if test="normalize-space(rm:Amount/text())">
            <xsl:apply-templates select="rm:Unit[1]"/>
            <data field="pack_value"><xsl:value-of select="normalize-space(rm:Amount/text())"/></data>
        </xsl:if>
    </xsl:template>

    <xsl:template match="rm:Unit[rm:ValueListURN/text()='urn:sahana:eden:request:currency']">
        <xsl:if test="normalize-space(rm:Value[1]/text())">
            <data field="currency"><xsl:value-of select="normalize-space(rm:Value[1]/text())"/></data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ADDITIONAL DATA                                                    -->
    <!-- ****************************************************************** -->
    <!-- human_resource_records -->
    <xsl:template match="rm:ContactInformation" mode="human_resource">
        <resource name="hrm_human_resource">
            <xsl:call-template name="HumanResourceUID">
                <xsl:with-param name="contact" select="."/>
            </xsl:call-template>
            <data field="type" value="1"/>
            <data field="status" value="1"/>
            <reference field="person_id" resource="pr_person">
                <xsl:call-template name="PersonUID">
                    <xsl:with-param name="contact" select="."/>
                </xsl:call-template>
            </reference>
            <reference field="organisation_id" resource="org_organisation">
                <xsl:call-template name="OrganisationUID">
                    <xsl:with-param name="contact" select="."/>
                </xsl:call-template>
            </reference>
            <!-- TODO: site reference -->
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- pr_person records -->
    <xsl:template match="rm:ContactInformation" mode="person">
        <resource name="pr_person">
            <xsl:call-template name="PersonUID">
                <xsl:with-param name="contact" select="."/>
            </xsl:call-template>
            <data field="first_name"><xsl:value-of select="rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='FirstName']/text()"/></data>
            <data field="last_name"><xsl:value-of select="rm:AdditionalContactInformation/xpil:PartyName/xnl:PersonName/xnl:NameElement[@xnl:ElementType='LastName']/text()"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- org_organisation records -->
    <!-- TODO: allow import only if no UUID is given -->
    <xsl:template match="rm:ContactInformation" mode="organisation">
        <resource name="org_organisation">
            <xsl:call-template name="OrganisationUID">
                <xsl:with-param name="contact" select="."/>
            </xsl:call-template>
            <data field="name"><xsl:value-of select="rm:AdditionalContactInformation/xpil:PartyName/xnl:OrganisationName/xnl:NameElement[1]/text()"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- TODO: org_office (site) records (only when no UUID) -->

    <!-- ****************************************************************** -->
    <!-- supply_item records (only when no UUID) -->
    <xsl:template match="rm:Value[../rm:ValueListURN='urn:sahana:eden:request:items']"
                  mode="record">
        <xsl:if test="not(@s3:uuid)">
            <!-- TODO: incomplete? -->
            <resource name="supply_item">
                <xsl:call-template name="SupplyItemUID"/>
                <data field="name"><xsl:value-of select="text()"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- TODO: supply_item_pack records (only when no UUID) -->

    <!-- ****************************************************************** -->
    <!-- TODO: hrm_skill records (only when no UUID) -->

    <!-- ****************************************************************** -->
    <!-- Site references -->
    <xsl:template match="rm:ScheduleInformation[rm:ScheduleType/text()='ReportTo']"
                  mode="reference">
        <reference name="site_id">
            <!-- TODO: incomplete -->
        </reference>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HELPER TEMPLATES                                                   -->
    <!-- ****************************************************************** -->
    <!-- DateTime: split ISO-format strings into date and time strings -->
    <xsl:template name="DateTime">
        <xsl:param name="datetime"/>
        <xsl:param name="date"/>
        <xsl:param name="time"/>
        <xsl:variable name="datestr" select="substring-before($datetime, 'T')"/>
        <xsl:variable name="timestr">
            <xsl:choose>
                <xsl:when test="contains($datetime, 'Z')">
                    <xsl:value-of select="substring-before(substring-after($datetime, 'T'), 'Z')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="substring-after($datetime, 'T')"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <data>
            <xsl:attribute name="field"><xsl:value-of select="$date"/></xsl:attribute>
            <xsl:value-of select="$datestr"/>
        </data>
        <data>
            <xsl:attribute name="field"><xsl:value-of select="$time"/></xsl:attribute>
            <xsl:value-of select="$timestr"/>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hide everything else -->
    <xsl:template match="*"/>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
