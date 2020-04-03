<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Availability Slots: Date Formulae - CSV Import Stylesheet

         CSV fields:
         Name............................pr_date_formula.name
         Interval........................pr_date_formula.date_interval
         Rate............................pr_date_formula.rate
         Monday..........................pr_date_formula.days_of_week
         Tuesday.........................pr_date_formula.days_of_week
         Wednesday.......................pr_date_formula.days_of_week
         Thursday........................pr_date_formula.days_of_week
         Friday..........................pr_date_formula.days_of_week
         Saturday........................pr_date_formula.days_of_week
         Sunday..........................pr_date_formula.days_of_week

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Interval">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Interval']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="pr_date_formula">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:choose>
                <xsl:when test="$Interval='DAILY'">
                    <data field="date_interval">1</data>
                </xsl:when>
                <xsl:when test="$Interval='WEEKLY'">
                    <data field="date_interval">2</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Use System Default -->
                </xsl:otherwise>
            </xsl:choose>

            <data field="rate"><xsl:value-of select="col[@field='Rate']"/></data>

            <xsl:call-template name="DaysOfWeek"/>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="DaysOfWeek">
        <xsl:variable name="Monday">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Monday']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Tuesday">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Tuesday']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Wednesday">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Wednesday']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Thursday">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Thursday']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Friday">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Friday']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Saturday">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Saturday']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Sunday">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Sunday']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="DaysMonday">
            <xsl:choose>
                <xsl:when test="$Monday='Y'">
                    <xsl:text>1,</xsl:text>
                </xsl:when>
                <xsl:when test="$Monday='YES'">
                    <xsl:text>1,</xsl:text>
                </xsl:when>
                <xsl:when test="$Monday='T'">
                    <xsl:text>1,</xsl:text>
                </xsl:when>
                <xsl:when test="$Monday='TRUE'">
                    <xsl:text>1,</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume False -->
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="DaysTuesday">
            <xsl:choose>
                <xsl:when test="$Tuesday='Y'">
                    <xsl:value-of select="concat($DaysMonday, '2,')"/>
                </xsl:when>
                <xsl:when test="$Tuesday='YES'">
                    <xsl:value-of select="concat($DaysMonday, '2,')"/>
                </xsl:when>
                <xsl:when test="$Tuesday='T'">
                    <xsl:value-of select="concat($DaysMonday, '2,')"/>
                </xsl:when>
                <xsl:when test="$Tuesday='TRUE'">
                    <xsl:value-of select="concat($DaysMonday, '2,')"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume False -->
                    <xsl:value-of select="$DaysMonday"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="DaysWednesday">
            <xsl:choose>
                <xsl:when test="$Wednesday='Y'">
                    <xsl:value-of select="concat($DaysTuesday, '3,')"/>
                </xsl:when>
                <xsl:when test="$Wednesday='YES'">
                    <xsl:value-of select="concat($DaysTuesday, '3,')"/>
                </xsl:when>
                <xsl:when test="$Wednesday='T'">
                    <xsl:value-of select="concat($DaysTuesday, '3,')"/>
                </xsl:when>
                <xsl:when test="$Wednesday='TRUE'">
                    <xsl:value-of select="concat($DaysTuesday, '3,')"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume False -->
                    <xsl:value-of select="$DaysTuesday"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="DaysThursday">
            <xsl:choose>
                <xsl:when test="$Thursday='Y'">
                    <xsl:value-of select="concat($DaysWednesday, '4,')"/>
                </xsl:when>
                <xsl:when test="$Thursday='YES'">
                    <xsl:value-of select="concat($DaysWednesday, '4,')"/>
                </xsl:when>
                <xsl:when test="$Thursday='T'">
                    <xsl:value-of select="concat($DaysWednesday, '4,')"/>
                </xsl:when>
                <xsl:when test="$Thursday='TRUE'">
                    <xsl:value-of select="concat($DaysWednesday, '4,')"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume False -->
                    <xsl:value-of select="$DaysWednesday"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="DaysFriday">
            <xsl:choose>
                <xsl:when test="$Friday='Y'">
                    <xsl:value-of select="concat($DaysThursday, '5,')"/>
                </xsl:when>
                <xsl:when test="$Friday='YES'">
                    <xsl:value-of select="concat($DaysThursday, '5,')"/>
                </xsl:when>
                <xsl:when test="$Friday='T'">
                    <xsl:value-of select="concat($DaysThursday, '5,')"/>
                </xsl:when>
                <xsl:when test="$Friday='TRUE'">
                    <xsl:value-of select="concat($DaysThursday, '5,')"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume False -->
                    <xsl:value-of select="$DaysThursday"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="DaysSaturday">
            <xsl:choose>
                <xsl:when test="$Saturday='Y'">
                    <xsl:value-of select="concat($DaysFriday, '6,')"/>
                </xsl:when>
                <xsl:when test="$Saturday='YES'">
                    <xsl:value-of select="concat($DaysFriday, '6,')"/>
                </xsl:when>
                <xsl:when test="$Saturday='T'">
                    <xsl:value-of select="concat($DaysFriday, '6,')"/>
                </xsl:when>
                <xsl:when test="$Saturday='TRUE'">
                    <xsl:value-of select="concat($DaysFriday, '6,')"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume False -->
                    <xsl:value-of select="$DaysFriday"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="DaysSunday">
            <xsl:choose>
                <xsl:when test="$Sunday='Y'">
                    <xsl:value-of select="concat($DaysSaturday, '0')"/>
                </xsl:when>
                <xsl:when test="$Sunday='YES'">
                    <xsl:value-of select="concat($DaysSaturday, '0')"/>
                </xsl:when>
                <xsl:when test="$Sunday='T'">
                    <xsl:value-of select="concat($DaysSaturday, '0')"/>
                </xsl:when>
                <xsl:when test="$Sunday='TRUE'">
                    <xsl:value-of select="concat($DaysSaturday, '0')"/>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume False -->
                    <xsl:value-of select="$DaysSaturday"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="AllDays">
            <xsl:choose>
                <xsl:when test="substring($DaysSunday, string-length($DaysSunday), 1)=','">
                    <!-- Remove trailing comma -->
                    <xsl:value-of select="substring($DaysSunday, 1, string-length($DaysSunday) - 1)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$DaysSunday"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="Days">
            <xsl:value-of select="concat('[', $AllDays, ']')"/>
        </xsl:variable>

        <data field="days_of_week"><xsl:value-of select="$Days"/></data>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
