<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         RSS Export Templates for S3XRC

         Version 0.1 / 2010-06-17 / by nursix

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

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>
    <xsl:param name="title"/>
    <xsl:param name="prefix"/>
    <xsl:param name="name"/>
    <xsl:param name="id"/>
    <xsl:param name="component"/>
    <xsl:param name="mode"/>
    <xsl:param name="utcnow"/>

    <!-- ****************************************************************** -->
    <xsl:include href="base.xsl"/> <!-- Do not remove this line! -->

    <!-- ****************************************************************** -->
    <!-- pr_person -->
    <xsl:template match="resource[@name='pr_person']" mode="contents">
        <xsl:variable name="first_name" select="./data[@field='first_name']/text()"/>
        <xsl:variable name="middle_name" select="./data[@field='middle_name']/text()"/>
        <xsl:variable name="last_name" select="./data[@field='last_name']/text()"/>
        <title>
            <xsl:choose>
                <xsl:when test="$middle_name and $last_name">
                    <xsl:value-of select="concat($first_name, ' ', $middle_name, ' ', $last_name)"/>
                </xsl:when>
                <xsl:when test="$last_name">
                    <xsl:value-of select="concat($first_name, ' ', $last_name)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$first_name"/>
                </xsl:otherwise>
            </xsl:choose>
        </title>
        <description>
            <xsl:if test="./data[@field='pr_pe_label']/text()">
                <xsl:text>ID Label:</xsl:text>
                <xsl:value-of select="./data[@field='pr_pe_label']/text()"/>
            </xsl:if>
        </description>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- pr_presence -->
    <xsl:template match="resource[@name='pr_presence']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='time']/text()"/>
        </title>
        <description>
            &lt;b&gt;
            <xsl:value-of select="./data[@field='opt_pr_presence_condition']/text()"/>
            &lt;/b&gt;
            <xsl:text>: </xsl:text>
            <xsl:value-of select="./data[@field='location_details']/text()"/>
            <xsl:if test="./reference[@field='location_id']/text()">
                <xsl:value-of select="concat(' [',./reference[@field='location_id']/text(),']')"/>
            </xsl:if>
            <xsl:if test="./data[@field='proc_desc']/text()">
                &lt;br/&gt;
                <xsl:value-of select="./data[@field='proc_desc']/text()"/>
            </xsl:if>
        </description>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- rms_req -->
    <xsl:template match="resource[@name='rms_req']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='timestamp']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='message']/text()"/>
            <xsl:if test="./data[@field='source_type']/text()">
                &lt;br/&gt;
                <xsl:value-of select="concat('Source: ', ./data[@field='source_type']/text(), ' ')"/>
                <xsl:if test="./data[@field='source_id']/text()">
                    <xsl:value-of select="concat(' [', ./data[@field='source_id']/text(), ']')"/>
                </xsl:if>
            </xsl:if>
        </description>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- hms_hospital -->
    <xsl:template match="resource[@name='hms_hospital']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='name']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='city']/text()"/>
            <xsl:if test="./reference[@field='location_id']/text()">
                <xsl:value-of select="concat(' [', ./reference[@field='location_id']/text(), ']')"/>
            </xsl:if>
            &lt;br/&gt;&lt;br/&gt;
            <xsl:text>Facility Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./data[@field='facility_status']/text()">
                    <xsl:value-of select="./data[@field='facility_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Clinical Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./data[@field='clinical_status']/text()">
                    <xsl:value-of select="./data[@field='clinical_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Morgue Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./data[@field='morgue_status']/text()">
                    <xsl:value-of select="./data[@field='morgue_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Security Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="./data[@field='security_status']/text()">
                    <xsl:value-of select="./data[@field='security_status']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
            <xsl:text>Beds Available: </xsl:text>
            <xsl:choose>
                <xsl:when test="./data[@field='available_beds']/text()">
                    <xsl:value-of select="./data[@field='available_beds']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
            &lt;br/&gt;
        </description>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- hms_hrequest -->
    <xsl:template match="resource[@name='hms_hrequest']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='subject']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='message']/text()"/>
        </description>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- dvi_recreq -->
    <xsl:template match="resource[@name='dvi_recreq']" mode="contents">
        <title>
            <xsl:value-of select="./data[@field='marker']/text()"/>
        </title>
        <description>
            <xsl:value-of select="./data[@field='date']/text()"/>
        </description>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- supply_item_entity -->
    <!-- @ToDo: Add Virtual Fields -->
    <xsl:template match="resource[@name='supply_item_entity']" mode="contents">
        <xsl:variable name="Quantity" select="./data[@field='quantity']/text()"/>
        <xsl:variable name="UoM" select="./reference[@field='item_pack_id']/text()"/>
        <xsl:variable name="InstanceType" select="./data[@field='instance_type']/text()"/>
        <title>
            <xsl:value-of select="./reference[@field='item_id']/text()"/>
        </title>
        <description>
            <xsl:text>Quantity: </xsl:text>
            <xsl:value-of select="concat($Quantity, ' ',$UoM)"/>
            &lt;br/&gt;&lt;br/&gt;
            <xsl:text>Status: </xsl:text>
            <xsl:choose>
                <xsl:when test="contains($InstanceType, 'Inventory')">
                    <xsl:text>Stock</xsl:text>
                </xsl:when>
                <xsl:when test="contains($InstanceType, 'Order')">
                    <xsl:text>On Order</xsl:text>
                </xsl:when>
                <xsl:when test="contains($InstanceType, 'Planned')">
                    <xsl:text>Planned Procurement</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </description>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
