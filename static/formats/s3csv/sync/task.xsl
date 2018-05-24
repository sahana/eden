<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Sync Task Import

         CSV fields:

         Repository......................sync_repository.name
         Resource........................sync_task.resource_name
                                         table name or "mixed"
         Input File......................sync_task.infile_pattern
         Delete Input Files..............sync_task.delete_input_files
                                         true|false
         Output File.....................sync_task.outfile_pattern
         Human-readable Output...........sync_task.human_readable
                                         true|false
         Mode............................sync_task.mode
                                         PULL|PUSH|BOTH|NONE
         Strategy........................sync_task.strategy
                                         CREATE|UPDATE|DELETE|MERGE or ALL
                                         (multiple, separated by +)
         Update Policy...................sync_task.update_policy
                                         NEWER|THIS|OTHER|MASTER
                                         (default NEWER)
         Conflict Policy.................sync_task.conflict_policy
                                         NEWER|THIS|OTHER|MASTER
                                         (default NEWER)

    *********************************************************************** -->
    <xsl:import href="common.xsl"/>

    <xsl:output method="xml"/>

    <!-- Index for repositories -->
    <xsl:key name="repositories" match="row" use="col[@field='Repository']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Create repositories -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('repositories',
                                                                       col[@field='Repository'])[1])]">
                <xsl:call-template name="Repository"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Repository" select="col[@field='Repository']/text()"/>
        <xsl:variable name="Resource" select="col[@field='Resource']/text()"/>

        <xsl:if test="$Repository!='' and $Resource!=''">
            <resource name="sync_task">

                <reference field="repository_id" resource="sync_repository">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('REPOSITORY:', $Repository)"/>
                    </xsl:attribute>
                </reference>

                <!-- Resource Name -->
                <data field="resource_name">
                    <xsl:value-of select="$Resource"/>
                </data>

                <!-- Input File -->
                <xsl:variable name="InputFile" select="col[@field='Input File']/text()"/>
                <xsl:if test="$InputFile!=''">
                    <data field="infile_pattern">
                        <xsl:value-of select="$InputFile"/>
                    </data>
                </xsl:if>

                <!-- Delete Input Files? -->
                <xsl:variable name="DeleteInputFiles" select="col[@field='Delete Input Files']/text()"/>
                <data field="delete_input_files">
                    <xsl:attribute name="value">
                        <xsl:choose>
                            <xsl:when test="$DeleteInputFiles='true'">
                                <xsl:value-of select="'true'"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'false'"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </data>

                <!-- Output File -->
                <xsl:variable name="OutputFile" select="col[@field='Output File']/text()"/>
                <xsl:if test="$OutputFile!=''">
                    <data field="outfile_pattern">
                        <xsl:value-of select="$OutputFile"/>
                    </data>
                </xsl:if>

                <!-- Human-readable Output? -->
                <xsl:variable name="HumanReadable" select="col[@field='Human-readable Output']/text()"/>
                <data field="human_readable">
                    <xsl:attribute name="value">
                        <xsl:choose>
                            <xsl:when test="$HumanReadable='true'">
                                <xsl:value-of select="'true'"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'false'"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </data>

                <!-- Mode -->
                <xsl:variable name="Mode" select="col[@field='Mode']/text()"/>
                <xsl:if test="$Mode!=''">
                    <data field="mode">
                        <xsl:attribute name="value">
                            <xsl:choose>
                                <xsl:when test="$Mode='PULL'">1</xsl:when>
                                <xsl:when test="$Mode='PUSH'">2</xsl:when>
                                <xsl:when test="$Mode='BOTH'">3</xsl:when>
                                <xsl:when test="$Mode='NONE'">4</xsl:when>
                            </xsl:choose>
                        </xsl:attribute>
                    </data>
                </xsl:if>

                <!-- Strategy -->
                <xsl:variable name="Strategy">
                    <xsl:call-template name="Strategy">
                        <xsl:with-param name="List">
                            <xsl:choose>
                                <xsl:when test="col[@field='Strategy']/text()='ALL'">
                                    <xsl:text>CREATE+UPDATE+DELETE+MERGE</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="col[@field='Strategy']/text()"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:if test="$Strategy!=''">
                    <data field="strategy">
                        <xsl:attribute name="value">
                            <xsl:value-of select="concat('[', substring-after($Strategy, ',') ,']')"/>
                        </xsl:attribute>
                    </data>
                </xsl:if>

                <!-- Update Policy -->
                <xsl:variable name="UpdatePolicy" select="col[@field='Update Policy']/text()"/>
                <xsl:if test="$UpdatePolicy!=''">
                    <data field="update_policy">
                        <xsl:choose>
                            <xsl:when test="$Mode='THIS'">THIS</xsl:when>
                            <xsl:when test="$Mode='OTHER'">OTHER</xsl:when>
                            <xsl:when test="$Mode='MASTER'">MASTER</xsl:when>
                            <xsl:otherwise>NEWER</xsl:otherwise>
                        </xsl:choose>
                    </data>
                </xsl:if>

                <!-- Conflict Policy -->
                <xsl:variable name="ConflictPolicy" select="col[@field='Conflict Policy']/text()"/>
                <xsl:if test="$ConflictPolicy!=''">
                    <data field="conflict_policy">
                        <xsl:choose>
                            <xsl:when test="$Mode='THIS'">THIS</xsl:when>
                            <xsl:when test="$Mode='OTHER'">OTHER</xsl:when>
                            <xsl:when test="$Mode='MASTER'">MASTER</xsl:when>
                            <xsl:otherwise>NEWER</xsl:otherwise>
                        </xsl:choose>
                    </data>
                </xsl:if>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template for Strategy Value -->
    <xsl:template name="Strategy">
        <xsl:param name="List"/>

        <xsl:variable name="tail">
            <xsl:variable name="remainder" select="substring-after($List, '+')"/>
            <xsl:if test="$remainder!=''">
                <xsl:call-template name="Strategy">
                    <xsl:with-param name="List">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:if>
        </xsl:variable>

        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="contains($List, '+')">
                    <xsl:value-of select="substring-before($List, '+')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$List"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$head='CREATE'">
                <xsl:value-of select="concat(',&quot;create&quot;', $tail)"/>
            </xsl:when>
            <xsl:when test="$head='UPDATE'">
                <xsl:value-of select="concat(',&quot;update&quot;', $tail)"/>
            </xsl:when>
            <xsl:when test="$head='DELETE'">
                <xsl:value-of select="concat(',&quot;delete&quot;', $tail)"/>
            </xsl:when>
            <xsl:when test="$head='MERGE'">
                <xsl:value-of select="concat(',&quot;merge&quot;', $tail)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$tail"/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
