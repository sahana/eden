<?xml version="1.0"?>
<xsl:stylesheet
    xmlns="urn:oasis:names:tc:emergency:EDXL:DE:1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:rm="urn:oasis:names:tc:emergency:EDXL:RM:1.0:msg"
    xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3"
    xmlns:xnl="urn:oasis:names:tc:cqi:xnl:3"
    xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
    xmlns:s3="urn:sahana:eden:s3">

    <!-- **********************************************************************

         EDXL-RM Export Templates

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

    <!-- Parameters passed from the back-end -->
    <xsl:param name="msguid"/>
    <xsl:param name="utcnow"/>
    <xsl:param name="domain"/>
    <xsl:param name="mode"/>

    <!-- ****************************************************************** -->
    <!-- Document node -->
    <xsl:template match="/">
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Root element -->
    <xsl:template match="s3xml">
        <EDXLDistribution>
            <!-- @todo: put this into a EDXL common -->
            <!-- @todo: provide header data from the back-end -->
            <distributionID><xsl:value-of select="$msguid"/></distributionID>
            <senderID>sahana@<xsl:value-of select="$domain"/></senderID>
            <dateTimeSent><xsl:value-of select="$utcnow"/></dateTimeSent>
            <distributionStatus>Actual</distributionStatus>
            <distributionType>
                <xsl:choose>
                    <xsl:when test="$mode='request'">Request</xsl:when>
                    <xsl:otherwise>Response</xsl:otherwise>
                </xsl:choose>
            </distributionType>
            <combinedConfidentiality>Unclassified</combinedConfidentiality>
            <xsl:apply-templates select="resource[@name='req_req']"/>
        </EDXLDistribution>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Content Type -->
    <xsl:template match="resource[@name='req_req']">
        <xsl:variable name="type" select="./data[@field='type']/@value"/>
        <xsl:variable name="part" select="position()"/>
        <contentObject>
            <xmlContent>
                <embeddedXMLContent>
                    <xsl:choose>
                        <xsl:when test="$mode='request'">
                            <xsl:call-template name="RequestResource">
                                <xsl:with-param name="type" select="$type"/>
                                <xsl:with-param name="part" select="$part"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="ResponseToRequestResource">
                                <xsl:with-param name="type" select="$type"/>
                                <xsl:with-param name="part" select="$part"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </embeddedXMLContent>
            </xmlContent>
        </contentObject>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- RequestResourceProlog -->
    <xsl:template name="RequestResource">
        <xsl:param name="type"/>
        <xsl:variable name="deliver_to">
            <xsl:choose>
                <xsl:when test="$type=1">Deliver to</xsl:when>
                <xsl:otherwise>Report to</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <rm:RequestResource>
            <rm:MessageID><xsl:value-of select="./data[@field='request_number']"/></rm:MessageID>
            <xsl:call-template name="SentDateTime"/>
            <rm:MessageContentType>RequestResource</rm:MessageContentType>
            <xsl:call-template name="OriginatingMessageID"/>
            <xsl:call-template name="IncidentInformation"/>
            <!-- Requested by -->
            <xsl:call-template name="ContactInformation">
                <xsl:with-param name="role">Requester</xsl:with-param>
                <xsl:with-param name="contact" select="./reference[@field='requester_id']/@uuid"/>
            </xsl:call-template>
            <!-- Requested for -->
            <xsl:call-template name="ContactInformation">
                <xsl:with-param name="description" select="$deliver_to"/>
                <xsl:with-param name="contact" select="./reference[@field='request_for_id']/@uuid"/>
            </xsl:call-template>
            <xsl:choose>
                <xsl:when test="$type=1">
                    <xsl:apply-templates select="./resource[@name='req_req_item']" mode="Donation"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="./resource[@name='req_req_item']" mode="Volunteer"/>
                </xsl:otherwise>
            </xsl:choose>
        </rm:RequestResource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ResponseToRequestResource Prolog -->
    <xsl:template name="ResponseToRequestResource">
        <xsl:param name="type"/>
        <xsl:param name="part"/>
        <xsl:variable name="delivered_to">
            <xsl:choose>
                <xsl:when test="$type=1">Delivered to</xsl:when>
                <xsl:otherwise>Reported to</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="mode">
            <xsl:choose>
                <xsl:when test="$type=1">Donation</xsl:when>
                <xsl:otherwise>Volunteer</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <rm:ResponseToRequestResource>
            <rm:MessageID><xsl:value-of select="concat($msguid, '-', $part)"/></rm:MessageID>
            <xsl:call-template name="SentDateTime"/>
            <rm:MessageContentType>ResponseToRequestResource</rm:MessageContentType>
            <xsl:call-template name="OriginatingMessageID"/>
            <xsl:call-template name="IncidentInformation"/>
            <xsl:call-template name="ContactInformation">
                <xsl:with-param name="role">RespondingOrg</xsl:with-param>
                <xsl:with-param name="contact" select="./reference[@field='assigned_to_id']/@uuid"/>
            </xsl:call-template>
            <xsl:call-template name="ContactInformation">
                <xsl:with-param name="role">Approver</xsl:with-param>
                <xsl:with-param name="contact" select="./reference[@field='approved_by_id']/@uuid"/>
            </xsl:call-template>
            <xsl:call-template name="ContactInformation">
                <xsl:with-param name="description" select="$delivered_to"/>
                <xsl:with-param name="contact" select="./reference[@field='recv_by_id']/@uuid"/>
            </xsl:call-template>
            <!-- Surplus Disposal? -->
            <xsl:choose>
                <xsl:when test="$type=1">
                    <xsl:apply-templates select="./resource[@name='req_req_item']"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="./resource[@name='req_req_skill']"/>
                </xsl:otherwise>
            </xsl:choose>
        </rm:ResponseToRequestResource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ContactInformation -->
    <xsl:template name="ContactInformation">
        <xsl:param name="contact"/>
        <xsl:param name="role"/>
        <xsl:param name="description"/>
        <rm:ContactInformation>
            <xsl:choose>
                <xsl:when test="$role!=''">
                    <rm:ContactRole><xsl:value-of select="$role"/></rm:ContactRole>
                </xsl:when>
                <xsl:otherwise>
                    <rm:ContactDescription><xsl:value-of select="$description"/></rm:ContactDescription>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:apply-templates
                select="/s3xml/resource[@name='hrm_human_resource' and @uuid=$contact]"/>
        </rm:ContactInformation>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HELPER TEMPLATES                                                   -->
    <!-- ****************************************************************** -->
    <!-- OriginatingMessageID from request_number -->
    <xsl:template name="OriginatingMessageID">
        <rm:OriginatingMessageID><xsl:value-of select="./data[@field='request_number']"/></rm:OriginatingMessageID>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- SentDateTime -->
    <xsl:template name="SentDateTime">
        <!-- is this the current UTC or the request create time? -->
        <rm:SentDateTime><xsl:value-of select="$utcnow"/></rm:SentDateTime>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- IncidentInformation -->
    <xsl:template name="IncidentInformation">
        <rm:IncidentInformation s3:uuid="UUID goes here">
            <xsl:attribute name="s3:uuid">
                <xsl:value-of select="reference[@field='event_id']/@uuid"/>
            </xsl:attribute>
            <rm:IncidentDescription>
                <xsl:value-of select="reference[@field='event_id']/text()"/>
            </rm:IncidentDescription>
        </rm:IncidentInformation>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- AdditionalContactInformation from hrm_human_resource -->
    <xsl:template match="resource[@name='hrm_human_resource']">
        <rm:AdditionalContactInformation>
            <xsl:variable name="person_uuid" select="./reference[@field='person_id']/@uuid"/>
            <xsl:variable name="office_uuid" select="./reference[@field='site_id']/@uuid"/>
            <xsl:variable name="organisation_uuid" select="./reference[@field='organisation_id']/@uuid"/>
            <xpil:PartyName>
                <xsl:attribute name="xpil:ID"><xsl:value-of select="@uuid"/></xsl:attribute>
                <xsl:apply-templates
                    select="/s3xml/resource[@name='pr_person' and @uuid=$person_uuid]"/>
                <xsl:apply-templates
                    select="/s3xml/resource[@name='org_organisation' and @uuid=$organisation_uuid]"/>
            </xpil:PartyName>
            <!-- What about other site types? -->
            <!-- What about HR's without office (volunteers?), must switch to pr_contact then -->
            <xsl:apply-templates
                    select="/s3xml/resource[@name='org_office' and @uuid=$office_uuid]"/>
        </rm:AdditionalContactInformation>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- PersonName from pr_person -->
    <xsl:template match="resource[@name='pr_person']">
        <xnl:PersonName>
            <xsl:attribute name="xnl:Identifier"><xsl:value-of select="@uuid"/></xsl:attribute>
            <xnl:NameElement xnl:ElementType="FirstName"><xsl:value-of select="data[@field='first_name']/text()"/></xnl:NameElement>
            <xnl:NameElement xnl:ElementType="LastName"><xsl:value-of select="data[@field='last_name']/text()"/></xnl:NameElement>
            <!-- Job role? -->
        </xnl:PersonName>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- OrganisationName from org_organisation -->
    <xsl:template match="resource[@name='org_organisation']">
        <xnl:OrganisationName>
            <xsl:attribute name="xnl:Identifier"><xsl:value-of select="@uuid"/></xsl:attribute>
            <xnl:NameElement><xsl:value-of select="data[@field='name']/text()"/></xnl:NameElement>
        </xnl:OrganisationName>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ContactNumbers and ElectronicAddressIdentifiers from org_office -->
    <xsl:template match="resource[@name='org_office']">
        <xpil:ContactNumbers>
            <!-- alternative phone number? Fax number? -->
            <xpil:ContactNumber xpil:CommunicationsMediaType="Telephone">
                <xpil:ContactNumberElement><xsl:value-of select="data[@field='phone1']"/></xpil:ContactNumberElement>
            </xpil:ContactNumber>
        </xpil:ContactNumbers>
        <xpil:ElectronicAddressIdentifiers>
            <xpil:ElectronicAddressIdentifier xpil:Type="EMAIL"><xsl:value-of select="data[@field='email']"/></xpil:ElectronicAddressIdentifier>
        </xpil:ElectronicAddressIdentifiers>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Resource Information Donation -->
    <xsl:template match="resource[@name='req_req_item']">
        <rm:ResourceInformation>
            <rm:ResourceInfoElementID>
                <xsl:value-of select="@uuid"/>
            </rm:ResourceInfoElementID>
            <rm:Resource>
                <rm:Name>Donation</rm:Name>
                <!-- Item Type -->
                <xsl:call-template name="ResourceTypeStructure">
                    <xsl:with-param name="item_id" select="reference[@field='item_id']/@uuid"/>
                </xsl:call-template>
                <!-- Description -->
                <xsl:apply-templates select="data[@field='comments']"/>
                <!-- Priority -->
                <xsl:apply-templates select="../data[@field='priority']"/>
                <!-- Target Audience -->
                <xsl:comment>Target Audience: not implemented yet</xsl:comment>
                <!-- Target Organisation -->
                <xsl:comment>Target Organisation: not implemented yet</xsl:comment>
                <!-- Response Information -->
                <xsl:if test="$mode!='request'">
                    <xsl:call-template name="ResponseInformation"/>
                </xsl:if>
                <!-- Resource Status -->
                <xsl:if test="$mode!='request'">
                    <xsl:call-template name="ResourceStatus"/>
                </xsl:if>
                <!-- Assignment Information -->
                <rm:AssignmentInformation>
                    <!-- Purpose -->
                    <xsl:apply-templates select="../data[@field='purpose']"/>
                    <!-- Quantity -->
                    <xsl:call-template name="Quantity"/>
                    <!-- Restrictions: Security required, Transportation required -->
                    <xsl:call-template name="Restrictions"/>
                    <xsl:if test="$mode!='request'">
                        <xsl:call-template name="PriceQuote"/>
                    </xsl:if>
                </rm:AssignmentInformation>
                <!-- Requested From DateTime -->
                <xsl:call-template name="ScheduleDateTime">
                    <xsl:with-param name="type" select="string('RequestedArrival')"/>
                    <xsl:with-param name="date" select="string('date_required')"/>
                    <xsl:with-param name="time" select="string('time_required')"/>
                </xsl:call-template>
                <!-- Received DateTime -->
                <xsl:call-template name="ScheduleDateTime">
                    <xsl:with-param name="type">ActualReceived</xsl:with-param>
                    <xsl:with-param name="date">date_recv</xsl:with-param>
                    <xsl:with-param name="time">time_recv</xsl:with-param>
                </xsl:call-template>
                <!-- ReportTo Location -->
                <xsl:call-template name="ScheduleLocation">
                    <xsl:with-param name="type" select="string('ReportTo')"/>
                    <xsl:with-param name="site" select="../reference[@field='site_id']/@uuid"/>
                </xsl:call-template>
            </rm:Resource>
        </rm:ResourceInformation>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Resource Information Volunteer (not implemented yet) -->
    <xsl:template match="resource[@name='req_req_skill']">
        <rm:ResourceInformation>
            <rm:ResourceInfoElementID>
                <xsl:value-of select="@uuid"/>
            </rm:ResourceInfoElementID>
            <rm:Resource>
                <rm:Name>Volunteer</rm:Name>
                <!-- Description -->
                <xsl:apply-templates select="data[@field='comments']"/>
                <!-- Skills as list of keywords -->
                <rm:Keyword>
                    <rm:ValueListURN>urn:sahana:eden:skills</rm:ValueListURN>
                    <xsl:variable name="skill_id" select="substring-after(substring-before(reference[@field='skill_id']/@uuid, ']'), '[')"/>
                    <xsl:call-template name="SkillList">
                        <xsl:with-param name="skill_id" select="$skill_id"/>
                    </xsl:call-template>
                </rm:Keyword>
                <!-- Priority -->
                <xsl:apply-templates select="../data[@field='priority']"/>
                <!-- Target Audience -->
                <xsl:comment>Target Audience: not implemented yet</xsl:comment>
                <!-- Target Organisation -->
                <xsl:comment>Target Organisation: not implemented yet</xsl:comment>
                <!-- Response Information -->
                <xsl:if test="$mode!='request'">
                    <xsl:call-template name="ResponseInformation"/>
                </xsl:if>
                <!-- Resource Status -->
                <xsl:if test="$mode!='request'">
                    <xsl:call-template name="ResourceStatus"/>
                </xsl:if>
                <!-- Assignment Information -->
                <rm:AssignmentInformation>
                    <!-- Purpose -->
                    <xsl:apply-templates select="../data[@field='purpose']"/>
                    <!-- Quantity -->
                    <xsl:call-template name="NumberOfVolunteers"/>
                    <!-- Restrictions: Security required, Transportation required -->
                    <xsl:call-template name="Restrictions"/>
                </rm:AssignmentInformation>
                <!-- Requested From DateTime -->
                <xsl:call-template name="ScheduleDateTime">
                    <xsl:with-param name="type" select="string('RequestedArrival')"/>
                    <xsl:with-param name="date" select="string('date_required')"/>
                    <xsl:with-param name="time" select="string('time_required')"/>
                </xsl:call-template>
                <!-- Received DateTime -->
                <xsl:call-template name="ScheduleDateTime">
                    <xsl:with-param name="type">ActualReceived</xsl:with-param>
                    <xsl:with-param name="date">date_recv</xsl:with-param>
                    <xsl:with-param name="time">time_recv</xsl:with-param>
                </xsl:call-template>
                <!-- ReportTo Location -->
                <xsl:call-template name="ScheduleLocation">
                    <xsl:with-param name="type" select="string('ReportTo')"/>
                    <xsl:with-param name="site" select="../reference[@field='site_id']/@uuid"/>
                </xsl:call-template>
            </rm:Resource>
        </rm:ResourceInformation>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Resource Type (Items) -->
    <xsl:template name="ResourceTypeStructure">
        <xsl:param name="item_id"/>
        <rm:TypeStructure>
            <rm:ValueListURN>urn:sahana:eden:request:items</rm:ValueListURN>
            <rm:Value>
                <xsl:attribute name="s3:uuid">
                    <xsl:value-of select="$item_id"/>
                </xsl:attribute>
                <xsl:value-of select="/s3xml/resource[@name='supply_item' and @uuid=$item_id]/data[@field='name']/text()"/>
            </rm:Value>
        </rm:TypeStructure>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Build a list of skills -->
    <xsl:template name="SkillList">
        <xsl:param name="skill_id"/>
        <xsl:variable name="first">
            <xsl:choose>
                <xsl:when test="contains($skill_id, ',')">
                    <xsl:value-of select="substring-before($skill_id, ',')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$skill_id"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="uuid">
            <xsl:value-of select="normalize-space(substring-before(substring-after($first, '&quot;'), '&quot;'))"/>
        </xsl:variable>
        <rm:Value>
            <xsl:attribute name="s3:uuid">
                <xsl:value-of select="$uuid"/>
            </xsl:attribute>
            <xsl:value-of select="//resource[@name='hrm_skill' and @uuid=$uuid]/data[@field='name']/text()"/>
        </rm:Value>
        <xsl:if test="contains($skill_id, ',')">
            <xsl:call-template name="SkillList">
                <xsl:with-param name="skill_id" select="substring-after($skill_id, ',')"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Priority -->
    <xsl:template match="data[@field='priority']">
        <rm:Keyword>
            <rm:ValueListURN>urn:sahana:eden:request:priority</rm:ValueListURN>
            <rm:Value>
                <xsl:choose>
                    <xsl:when test="@value=3">High</xsl:when>
                    <xsl:when test="@value=2">Medium</xsl:when>
                    <xsl:otherwise>Low</xsl:otherwise>
                </xsl:choose>
            </rm:Value>
        </rm:Keyword>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Purpose -->
    <xsl:template match="data[@field='purpose']">
        <rm:AnticipatedFunction>
            <xsl:value-of select="./text()"/>
        </rm:AnticipatedFunction>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Comments -->
    <xsl:template match="data[@field='comments']">
        <xsl:if test="normalize-space(text())">
            <rm:Description>
                <xsl:value-of select="normalize-space(text())"/>
            </rm:Description>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ResponseInformation: accept or cancel -->
    <xsl:template name="ResponseInformation">
        <rm:ResponseInformation>
            <rm:PrecedingResourceInfoElementID>
                <xsl:value-of select="@uuid"/>
            </rm:PrecedingResourceInfoElementID>
            <rm:ResponseType>
                <xsl:choose>
                    <xsl:when test="../data[@field='cancel']/@value='false'">Accept</xsl:when>
                    <xsl:otherwise>Cancel</xsl:otherwise>
                </xsl:choose>
            </rm:ResponseType>
        </rm:ResponseInformation>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Resource Status: deployment and availability -->
    <xsl:template name="ResourceStatus">
        <rm:ResourceStatus>
            <rm:DeploymentStatus>
                <rm:ValueListURN>urn:sahana:eden:request:status</rm:ValueListURN>
                <xsl:variable name="commit_status" select="data[@field='commit_status']/@value"/>
                <xsl:variable name="fulfil_status" select="data[@field='fulfil_status']/@value"/>
                <rm:Value>
                    <xsl:choose>
                        <xsl:when test="$commit_status=1">Committed:Partial</xsl:when>
                        <xsl:when test="$commit_status=2">Committed:Full</xsl:when>
                        <xsl:otherwise>Committed:None</xsl:otherwise>
                    </xsl:choose>
                </rm:Value>
                <rm:Value>
                    <xsl:choose>
                        <xsl:when test="$fulfil_status=1">Fulfilled:Partial</xsl:when>
                        <xsl:when test="$fulfil_status=2">Fulfilled:Full</xsl:when>
                        <xsl:otherwise>Fulfilled:None</xsl:otherwise>
                    </xsl:choose>
                </rm:Value>
            </rm:DeploymentStatus>
            <rm:Availability>
                <xsl:value-of select="concat('QuantityCommitted:',
                                             data[@field='quantity_commit']/text())"/>
            </rm:Availability>
            <rm:Availability>
                <xsl:value-of select="concat('QuantityFulfilled:',
                                             data[@field='quantity_fulfil']/text())"/>
            </rm:Availability>
            <rm:Availability>
                <xsl:value-of select="concat('QuantityInTransit:',
                                             data[@field='quantity_transit']/text())"/>
            </rm:Availability>
        </rm:ResourceStatus>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Quantity (for items) -->
    <xsl:template name="Quantity">
        <rm:Quantity>
            <rm:MeasuredQuantity>
                <rm:Unit>
                    <rm:ValueListURN>urn:sahana:eden:request:pack:units</rm:ValueListURN>
                    <xsl:variable name="unit_id" select="reference[@field='item_pack_id']/@uuid"/>
                    <xsl:apply-templates select="//resource[@name='supply_item_pack' and @uuid=$unit_id]"/>
                </rm:Unit>
                <rm:Amount><xsl:value-of select="data[@field='quantity']/text()"/></rm:Amount>
            </rm:MeasuredQuantity>
        </rm:Quantity>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Quantity (for volunteers) -->
    <xsl:template name="NumberOfVolunteers">
        <rm:Quantity>
            <rm:MeasuredQuantity>
                <rm:Amount><xsl:value-of select="data[@field='quantity']/text()"/></rm:Amount>
            </rm:MeasuredQuantity>
        </rm:Quantity>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Price Quote: value per unit -->
    <xsl:template name="PriceQuote">
        <rm:PriceQuote>
            <rm:MeasuredQuantity>
                <rm:Unit>
                    <rm:ValueListURN>urn:sahana:eden:request:currency</rm:ValueListURN>
                    <rm:Value><xsl:value-of select="data[@field='currency']/text()"/></rm:Value>
                </rm:Unit>
                <rm:Amount><xsl:value-of select="data[@field='pack_value']/text()"/></rm:Amount>
            </rm:MeasuredQuantity>
        </rm:PriceQuote>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Restrictions (transportation required, security required) -->
    <xsl:template name="Restrictions">
        <rm:Restrictions>
            <xsl:variable name="transport">
                <xsl:choose>
                    <xsl:when test="../data[@field='transport_req']/@value!='false'">yes</xsl:when>
                    <xsl:otherwise>no</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="security">
                <xsl:choose>
                    <xsl:when test="../data[@field='security_req']/@value!='false'">yes</xsl:when>
                    <xsl:otherwise>no</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:value-of select="concat('TransportationRequired:', $transport, ',',
                                         'SecurityRequired:', $security)"/>
        </rm:Restrictions>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Package -->
    <xsl:template match="resource[@name='supply_item_pack']">
        <rm:Value>
            <xsl:attribute name="s3:uuid">
                <xsl:value-of select="@uuid"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="data[@field='quantity']/text()">
                    <xsl:value-of select="concat(data[@field='name']/text(), ' [quantity: ', data[@field='quantity']/text(), ']')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="data[@field='name']/text()"/>
                </xsl:otherwise>
            </xsl:choose>
        </rm:Value>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ScheduleInformation - DateTime -->
    <xsl:template name="ScheduleDateTime">
        <xsl:param name="type"/>
        <xsl:param name="date"/>
        <xsl:param name="time"/>
        <xsl:if test="../data[@field=$date]/text()">
            <xsl:variable name="timestr">
                <xsl:choose>
                    <xsl:when test="../data[@field=$time]/text()">
                        <xsl:value-of select="../data[@field=$time]/text()"/>
                    </xsl:when>
                    <xsl:otherwise>08:00:00</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <rm:ScheduleInformation>
                <rm:ScheduleType><xsl:value-of select="$type"/></rm:ScheduleType>
                <rm:DateTime>
                    <xsl:value-of select="concat(../data[@field=$date]/text(), 'T', $timestr)"/>
                </rm:DateTime>
            </rm:ScheduleInformation>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ScheduleInformation - Location -->
    <xsl:template name="ScheduleLocation">
        <xsl:param name="type"/>
        <xsl:param name="site"/>
        <xsl:variable name="site_info" select="//resource[@uuid=$site]"/>
        <xsl:if test="$site_info">
            <rm:ScheduleInformation>
                <rm:ScheduleType><xsl:value-of select="$type"/></rm:ScheduleType>
                <rm:Location>
                    <xal:Address>
                        <!-- Address -->
                        <xal:Premises>
                            <xal:Identifier><xsl:value-of select="$site_info/@uuid"/></xal:Identifier>
                            <xal:NameElement><xsl:value-of select="$site_info/data[@field='name']/text()"/></xal:NameElement>
                        </xal:Premises>
                        <xsl:variable name="location_id" select="$site_info/reference[@field='location_id']/@uuid"/>
                        <xsl:if test="$location_id">
                            <xsl:apply-templates select="//resource[@name='gis_location' and @uuid=$location_id]"/>
                        </xsl:if>
                    </xal:Address>
                </rm:Location>
            </rm:ScheduleInformation>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Location hierarchy specific for the US -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:choose>
            <xsl:when test="data[@field='level']/text()='Country'">
                <xal:Country>
                    <xsl:attribute name="s3:uuid">
                        <xsl:value-of select="@uuid"/>
                    </xsl:attribute>
                    <xal:Identifier><xsl:value-of select="data[@field='code']/text()"/></xal:Identifier>
                </xal:Country>
            </xsl:when>
            <xsl:when test="data[@field='level']/text()='L1'">
                <xal:AdministrativeArea xal:Type="state">
                    <xsl:attribute name="s3:uuid">
                        <xsl:value-of select="@uuid"/>
                    </xsl:attribute>
                    <!-- Abbreviation not available -->
                    <!-- <xal:NameElement Abbreviation="true">CA</xal:NameElement> -->
                    <xal:NameElement><xsl:value-of select="data[@field='name']/text()"/></xal:NameElement>
                </xal:AdministrativeArea>
            </xsl:when>
            <xsl:when test="data[@field='level']/text()='L2'">
                <xal:Locality xal:Type="city">
                    <xsl:attribute name="s3:uuid">
                        <xsl:value-of select="@uuid"/>
                    </xsl:attribute>
                    <xal:Name><xsl:value-of select="data[@field='name']/text()"/></xal:Name>
                </xal:Locality>
            </xsl:when>
            <xsl:when test="data[@field='level']/text()='L3'">
                <xal:Locality xal:Type="neighborhood">
                    <xsl:attribute name="s3:uuid">
                        <xsl:value-of select="@uuid"/>
                    </xsl:attribute>
                    <xal:Name><xsl:value-of select="data[@field='name']/text()"/></xal:Name>
                </xal:Locality>
           </xsl:when>
           <xsl:otherwise>
                <xsl:if test="data[@field='addr_street']/text()!=', '">
                    <xal:Thoroughfare>
                        <xsl:attribute name="s3:uuid">
                            <xsl:value-of select="@uuid"/>
                        </xsl:attribute>
                        <xsl:if test="data[@field='addr_street']/text()!=', '">
                            <xal:NameElement><xsl:value-of select="data[@field='addr_street']/text()"/></xal:NameElement>
                        </xsl:if>
                    </xal:Thoroughfare>
                    <xsl:if test="data[@field='addr_postcode']/text()!=''">
                        <xal:Postcode>
                            <xal:Identifier><xsl:value-of select="data[@field='addr_postcode']/text()"/></xal:Identifier>
                        </xal:Postcode>
                    </xsl:if>
                </xsl:if>
           </xsl:otherwise>
        </xsl:choose>
        <xsl:variable name="parent_uuid" select="reference[@field='parent']/@uuid"/>
        <xsl:if test="$parent_uuid">
            <xsl:apply-templates select="//resource[@name='gis_location' and @uuid=$parent_uuid]"/>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hide everything else -->
    <xsl:template match="*"/>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
