<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    
    <!-- Templates for Import of CSV Salary Information,
         used by: staff_level.xsl, salary_grade.xsl and person.xsl 
    -->

    <!-- ****************************************************************** -->
    <!-- Staff Level -->
    <xsl:template name="StaffLevel">

        <xsl:param name="Field">Name</xsl:param>

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Name" select="col[@field=$Field]"/>

        <xsl:if test="$Name!=''">
            <resource name="hrm_staff_level">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('StaffLevel:', $OrgName, ':', $Name)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
                <!-- Link to Organisation -->
                <xsl:if test="$OrgName!=''">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OrgName"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Salary Grade -->
    <xsl:template name="SalaryGrade">

        <xsl:param name="Field">Name</xsl:param>

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Name" select="col[@field=$Field]"/>

        <xsl:if test="$Name!=''">
            <resource name="hrm_salary_grade">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('SalaryGrade:', $OrgName, ':', $Name)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
                <!-- Link to Organisation -->
                <xsl:if test="$OrgName!=''">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OrgName"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Salary Information per Person -->
    <xsl:template name="Salary">

        <xsl:param name="person_tuid"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        
        <resource name="hrm_salary">
            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$person_tuid"/>
                </xsl:attribute>
            </reference>

            <xsl:variable name="StaffLevel" select="col[@field='Staff Level']/text()"/>
            <xsl:if test="$StaffLevel!=''">
                <reference field="staff_level_id" resource="hrm_staff_level">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('StaffLevel:', $OrgName, ':', $StaffLevel)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:variable name="SalaryGrade" select="col[@field='Salary Grade']/text()"/>
            <xsl:if test="$SalaryGrade!=''">
                <reference field="salary_grade_id" resource="hrm_salary_grade">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('SalaryGrade:', $OrgName, ':', $SalaryGrade)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:variable name="MonthlyAmount" select="col[@field='Monthly Salary']/text()"/>
            <xsl:if test="$MonthlyAmount!=''">
                <data field="monthly_amount">
                    <xsl:value-of select="$MonthlyAmount"/>
                </data>
            </xsl:if>

            <xsl:variable name="SalaryStartDate" select="col[@field='Salary Start Date']/text()"/>
            <xsl:if test="$SalaryStartDate!=''">
                <data field="start_date">
                    <xsl:value-of select="$SalaryStartDate"/>
                </data>
            </xsl:if>

            <xsl:variable name="SalaryEndDate" select="col[@field='Salary End Date']/text()"/>
            <xsl:if test="$SalaryEndDate!=''">
                <data field="end_date">
                    <xsl:value-of select="$SalaryEndDate"/>
                </data>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
