<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Subscriptions - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         First Name.....................required.....person first name
         Middle Name....................optional.....person middle name
         Last Name......................optional.....person last name (required in some deployments)
         Email..........................required.....person email address
         Resource.......................required.....subscription_resource.resource
         URL............................required.....subscription_resource.url
         Filter.........................optional.....filter.query
         Notify On......................optional.....subscription.notify_on
         Frequency......................optional.....subscription.frequency
         Method.........................optional.....subscription.method

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="email" match="row" use="col[@field='Email']"/>
    <xsl:key name="filter" match="row" use="col[@field='Filter']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('email',
                                                        col[@field='Email'])[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Filters -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('filter',
                                                        col[@field='Filter'])[1])]">
                <xsl:call-template name="Filter"/>
            </xsl:for-each>

            <!-- Subscriptions -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="notify_on" select="col[@field='Notify On']"/>
        <xsl:variable name="frequency" select="col[@field='Frequency']"/>
        <xsl:variable name="method" select="col[@field='Method']"/>
        <xsl:variable name="filter" select="col[@field='Filter']"/>

        <!-- Subscription -->
        <resource name="pr_subscription">
            <xsl:if test="$notify_on!=''">
                <!-- @ToDo: Test for list:string -->
                <data field="notify_on">
                    <xsl:value-of select="$notify_on"/>
                </data>
            </xsl:if>
            <xsl:if test="$frequency!=''">
                <data field="frequency">
                    <xsl:value-of select="$frequency"/>
                </data>
            </xsl:if>
            <xsl:if test="$method!=''">
                <!-- @ToDo: Test for list:string -->
                <data field="method">
                    <xsl:value-of select="$method"/>
                </data>
            </xsl:if>

            <!-- Link to Person -->
            <reference field="pe_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Email']"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Filter -->
            <xsl:if test="$filter!=''">
                <reference field="filter_id" resource="pr_filter">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$filter"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Resource -->
            <resource name="pr_subscription_resource">
                <data field="resource">
                    <xsl:value-of select="col[@field='Resource']"/>
                </data>
                <data field="url">
                    <xsl:value-of select="col[@field='URL']"/>
                </data>
            </resource>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Filter">
        <xsl:variable name="filter" select="col[@field='Filter']"/>

        <xsl:if test="$filter!=''">
            <resource name="pr_filter">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$filter"/>
                </xsl:attribute>

                <data field="query"><xsl:value-of select="$filter"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="email" select="col[@field='Email']"/>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$email"/>
            </xsl:attribute>

            <!-- Person record -->
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>

            <resource name="pr_contact">
                <data field="contact_method" value="EMAIL"/>
                <data field="value"><xsl:value-of select="$email"/></data>
            </resource>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>

