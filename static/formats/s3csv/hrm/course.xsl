<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Courses - CSV Import Stylesheet

         CSV fields:
         Code............................hrm_course.code
         Name............................hrm_course.name
         Type............................hrm_course.type
         Organisation....................hrm_course.organisation_id
         Pass............................hrm_course.pass_mark
         Certificate.....................hrm_course_certificate.certificate_id
         Job Titles......................hrm_course_job_title.job_title_id
         Sectors.........................hrm_course_sector.sector_id

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="CertPrefix" select="'Cert:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="certs" match="row"
             use="col[@field='Certificate']"/>

    <xsl:key name="orgs" match="row"
             use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Certificates -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('certs',
                                                        col[@field='Certificate'])[1])]">
                <xsl:call-template name="Certificate"/>
            </xsl:for-each>

            <!-- Orgs -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Courses -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="CertName" select="col[@field='Certificate']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="JobTitles" select="col[@field='Job Titles']"/>
        <xsl:variable name="Sectors" select="col[@field='Sectors']"/>
        <xsl:variable name="Type" select="col[@field='Type']"/>

        <!-- Course -->
        <resource name="hrm_course">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <xsl:if test="$CertName!=''">
                <resource name="hrm_course_certificate">
                    <reference field="certificate_id" resource="hrm_certificate">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($CertPrefix, $CertName)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
            <xsl:if test="$Type!=''">
                <xsl:choose>
                    <xsl:when test="$Type='Staff'">
                        <data field="type"><xsl:text>1</xsl:text></data>
                    </xsl:when>
                    <xsl:when test="$Type='Volunteers'">
                        <data field="type"><xsl:text>2</xsl:text></data>
                    </xsl:when>
                    <xsl:when test="$Type='Deployables'">
                        <data field="type"><xsl:text>3</xsl:text></data>
                    </xsl:when>
                    <xsl:when test="$Type='Members'">
                        <data field="type"><xsl:text>4</xsl:text></data>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- No Type -->
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="col[@field='Pass']!=''">
                <data field="pass_mark"><xsl:value-of select="col[@field='Pass']"/></data>
            </xsl:if>
            <!-- Job Titles -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$JobTitles"/>
                </xsl:with-param>
                <xsl:with-param name="listsep" select="';'"/>
                <xsl:with-param name="arg">job_title_ref</xsl:with-param>
            </xsl:call-template>
            <!-- Sectors -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$Sectors"/>
                </xsl:with-param>
                <xsl:with-param name="listsep" select="';'"/>
                <xsl:with-param name="arg">sector_ref</xsl:with-param>
            </xsl:call-template>
            
        </resource>

        <!-- Job Titles -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$JobTitles"/></xsl:with-param>
            <xsl:with-param name="listsep" select="';'"/>
            <xsl:with-param name="arg">job_title_res</xsl:with-param>
        </xsl:call-template>

        <!-- Sectors -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Sectors"/></xsl:with-param>
            <xsl:with-param name="listsep" select="';'"/>
            <xsl:with-param name="arg">sector_res</xsl:with-param>
        </xsl:call-template>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Certificate">

        <xsl:variable name="CertName" select="col[@field='Certificate']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="hrm_certificate">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($CertPrefix, $CertName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CertName"/></data>
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Job Titles -->
            <xsl:when test="$arg='job_title_ref'">
                <resource name="hrm_course_job_title">
                    <reference field="job_title_id" resource="hrm_job_title">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$item"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='job_title_res'">
                <resource name="hrm_job_title">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$item"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
            <!-- Sectors -->
            <xsl:when test="$arg='sector_ref'">
                <resource name="hrm_course_sector">
                    <reference field="sector_id" resource="org_sector">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$item"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='sector_res'">
                <resource name="org_sector">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$item"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
