<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
         DVR Allowance - CSV Import Stylesheet

         CSV column........Hashtag.......Format..........Content

         ID................#PersonID.....string..........the person ID label
         First Name........#FirstName....string..........the first name
         Last Name.........#LastName.....string..........the last name
         Date of Birth.....#DOB..........date............the date of birth
         Period............#Period.......date............date of entitlement period
         Date..............#Date.........date............planned payment date
         Amount EUR........#AmountEUR....double..........the amount in EUR
         Amount..........................double..........the amount
         Currency........................string..........the currency code
         Comments........................string..........comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../commons.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="PersonLabel">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs">|ID|#|PersonID|</xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="FirstName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs">|First Name|#|FirstName|</xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="LastName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs">|Last Name|#|LastName|</xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="DateOfBirth">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs">|Date of Birth|#|DOB|</xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="AmountEUR">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs">|Amount EUR|#|AmountEUR|</xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="Amount" select="col[@field='Amount']/text()"/>
        <xsl:variable name="Currency" select="col[@field='Currency']/text()"/>

        <xsl:if test="($AmountEUR!='' or $Amount!='') and ($PersonLabel!='' or ($FirstName!='' and $LastName!='' and $DateOfBirth!=''))">

            <resource name="dvr_allowance">

                <!-- Link to person -->
                <reference field="person_id" resource="pr_person">
                    <resource name="pr_person">
                        <xsl:if test="$PersonLabel!=''">
                            <data field="pe_label">
                                <xsl:value-of select="$PersonLabel"/>
                            </data>
                        </xsl:if>
                        <data field="first_name">
                            <xsl:value-of select="$FirstName"/>
                        </data>
                        <data field="last_name">
                            <xsl:value-of select="$LastName"/>
                        </data>
                        <data field="date_of_birth">
                            <xsl:value-of select="$DateOfBirth"/>
                        </data>
                    </resource>
                </reference>

                <!-- Dates -->
                <xsl:variable name="Period">
                    <xsl:call-template name="GetColumnValue">
                        <xsl:with-param name="colhdrs">|Period|#|Period|</xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:if test="$Period!=''">
                    <data field="entitlement_period">
                        <xsl:value-of select="$Period"/>
                    </data>
                </xsl:if>

                <xsl:variable name="Date">
                    <xsl:call-template name="GetColumnValue">
                        <xsl:with-param name="colhdrs">|Date|#|Date|</xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:if test="$Date!=''">
                    <data field="date">
                        <xsl:value-of select="$Date"/>
                    </data>
                </xsl:if>

                <!-- Amount -->
                <xsl:choose>
                    <xsl:when test="$AmountEUR!=''">
                        <data field="amount">
                            <xsl:value-of select="$AmountEUR"/>
                        </data>
                        <data field="currency">EUR</data>
                    </xsl:when>
                    <xsl:otherwise>
                        <data field="amount">
                            <xsl:value-of select="$Amount"/>
                        </data>
                        <data field="currency">
                            <xsl:value-of select="$Currency"/>
                        </data>
                    </xsl:otherwise>
                </xsl:choose>

                <!-- Comments -->
                <data field="comments">
                    <xsl:value-of select="col[@field='Comments']/text()"/>
                </data>

            </resource>

        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Dummy for commons.xsl -->

    <xsl:template name="resource"/>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
