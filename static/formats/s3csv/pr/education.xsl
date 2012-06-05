<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Human Resources - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         First Name.....................required.....person first name
         Middle Name....................optional.....person middle name
         Last Name......................optional.....person last name (required in some deployments)
         Initials.......................optional.....person initials
         Email..........................required.....person email address
         Education Level................optional.....person education level of award
         Degree Name....................optional.....person education award
         Major..........................optional.....person education major
         Grade..........................optional.....person education grade
         Year...........................optional.....person education year
         Institute......................optional.....person education institute

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->        
    <xsl:key name="email"
             match="row"
             use="col[@field='Email']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('email',
                                                        col[@field='Email'])[1])]">
                <xsl:call-template name="Person">
                    <xsl:with-param name="email" select="col[@field='Email']"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <!-- Education -->
        <xsl:call-template name="Education">
            <xsl:with-param name="email" select="col[@field='Email']/text()"/>
            <xsl:with-param name="level" select="col[@field='Education Level']"/>
            <xsl:with-param name="name" select="col[@field='Degree Name']"/>
            <xsl:with-param name="major" select="col[@field='Major']"/>
            <xsl:with-param name="grade" select="col[@field='Grade']"/>
            <xsl:with-param name="year" select="col[@field='Year']"/>
            <xsl:with-param name="institute" select="col[@field='Institute']"/>
        </xsl:call-template>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:param name="email"/>

        <xsl:if test="$email!=''">
            <resource name="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$email"/>
                </xsl:attribute>

                <!-- Person record -->
                <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
                <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
                <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
                <data field="initials"><xsl:value-of select="col[@field='Initials']"/></data>

                <resource name="pr_contact">
                    <data field="contact_method" value="EMAIL"/>
                    <data field="value"><xsl:value-of select="$email"/></data>
                </resource>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Education">
        <xsl:param name="email"/>
        <xsl:param name="level"/>
        <xsl:param name="name"/>
        <xsl:param name="major"/>
        <xsl:param name="grade"/>
        <xsl:param name="year"/>
        <xsl:param name="institute"/>

        <xsl:if test="$name and $name!=''">
            <resource name="pr_education">
                <data field="level">
                    <xsl:value-of select="$level"/>
                </data>
                <data field="award">
                    <xsl:value-of select="$name"/>
                </data>
                <data field="major">
                    <xsl:value-of select="$major"/>
                </data>
                <data field="grade">
                    <xsl:value-of select="$grade"/>
                </data>
                <data field="year">
                    <xsl:value-of select="$year"/>
                </data>
                <data field="institute">
                    <xsl:value-of select="$institute"/>
                </data>
                <xsl:if test="$email!=''">
                <!-- Link to item -->
                    <reference field="person_id" resource="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$email"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>
</xsl:stylesheet>

