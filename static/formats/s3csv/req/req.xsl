<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         requests - CSV Import Stylesheet

         - use for import to req/req resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be req/req/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Scenario.......................scenario_scenario.name & event_event.scenario_id
         Event..........................event_event.name, & req_req.event_id
         Request Type...................req_req.type
         Request Number.................req_req.req_ref
         Date Requested.................req_req.date
         Time Requested.................req_req.time_requested
         Priority.......................req_req.priority
         Purpose........................req_req.purpose
         Date Required..................req_req.date_required
         Time Required..................req_req.time_required
         Requester......................req_req.requester_id & hrm_human_resource.id (lookup only)
         Assigned To....................req_req.assigned_to_id & hrm_human_resource.id (lookup only)
         Approved by....................req_req.approved_by_id & hrm_human_resource.id (lookup only)
         Requested for..................req_req.request_for_id & hrm_human_resource.id (lookup only)
         Requested for Facility.........req_req.site_id & org_site.site_id (lookup only)
         Transportation Required........req_req.transport_req
         Security Required..............req_req.security_req
         Date Delivered.................req_req.date_recv
         Time Delivered.................req_req.time_recv
         Received by....................req_req.recv_by_id & hrm_human_resource.id (lookup only)
         Comments.......................req_req.comments

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Create each record -->
            <xsl:for-each select="table/row">
            <!-- ********************************************************** -->
                <!-- Scenario -->
                <xsl:variable name="Scenario"><xsl:value-of select="col[@field='Scenario']"/></xsl:variable>
                <resource name="scenario_scenario">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Scenario"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$Scenario"/></data>
                </resource>

                <!-- Event -->
                <xsl:variable name="Event"><xsl:value-of select="col[@field='Event']"/></xsl:variable>
                <resource name="event_event">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Event"/>
                    </xsl:attribute>
                    <reference field="scenario_id" resource="scenario_scenario">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Scenario"/>
                        </xsl:attribute>
                    </reference>
                    <data field="name"><xsl:value-of select="$Event"/></data>
                </resource>

                <!-- Site -->
                <xsl:variable name="Site"><xsl:value-of select="col[@field='Requested for Facility']"/></xsl:variable>
                <resource name="inv_warehouse">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Site"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$Site"/></data>
                </resource>

                <!-- ********************************************************** -->
                <!--  Requester -->
                <!--  Person Record -->
                <xsl:variable name="pr_Requester"><xsl:value-of select="concat('pr_', col[@field='Requester'])"/></xsl:variable>
                <xsl:variable name="hrm_Requester"><xsl:value-of select="concat('hrm_', col[@field='Requester'])"/></xsl:variable>
                <xsl:variable name="reqFirstName"  select="substring-before(col[@field='Requester'],' ')"/>
                <xsl:variable name="reqLastName"  select="substring-after(col[@field='Requester'],' ')"/>
                <!-- Person record -->
                <resource name="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$pr_Requester"/>
                    </xsl:attribute>
                    <data field="first_name">
                        <xsl:value-of select="$reqFirstName"/>
                    </data>
                    <data field="last_name">
                        <xsl:value-of select="$reqLastName"/>
                    </data>
                </resource>
                <!-- HR  Requester -->
                <resource name="hrm_human_resource">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$hrm_Requester"/>
                    </xsl:attribute>
                    <reference field="person_id" resource="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$pr_Requester"/>
                        </xsl:attribute>
                    </reference>
                </resource>

                <!-- ********************************************************** -->
                <!--  Assigned To -->
                <!--  Person Record -->
                <xsl:variable name="pr_AssignedTo"><xsl:value-of select="concat('pr_', col[@field='Assigned To'])"/></xsl:variable>
                <xsl:variable name="hrm_AssignedTo"><xsl:value-of select="concat('hrm_', col[@field='Assigned To'])"/></xsl:variable>
                <xsl:variable name="assFirstName"  select="substring-before(col[@field='Assigned To'],' ')"/>
                <xsl:variable name="assLastName"  select="substring-after(col[@field='Assigned To'],' ')"/>
                <xsl:if test="col[@field='Assigned To']!=''">
                    <!-- Person record -->
                    <resource name="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$pr_AssignedTo"/>
                        </xsl:attribute>
                        <data field="first_name">
                            <xsl:value-of select="$assFirstName"/>
                        </data>
                        <data field="last_name">
                            <xsl:value-of select="$assLastName"/>
                        </data>
                    </resource>
                    <!-- HR  Requester -->
                    <resource name="hrm_human_resource">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$hrm_AssignedTo"/>
                        </xsl:attribute>
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$pr_AssignedTo"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- ********************************************************** -->
                <!--  Approver -->
                <!--  Person Record -->
                <xsl:variable name="pr_Approver"><xsl:value-of select="concat('pr_', col[@field='Approved by'])"/></xsl:variable>
                <xsl:variable name="hrm_Approver"><xsl:value-of select="concat('hrm_', col[@field='Approved by'])"/></xsl:variable>
                <xsl:variable name="appFirstName"  select="substring-before(col[@field='Approved by'],' ')"/>
                <xsl:variable name="appLastName"  select="substring-after(col[@field='Approved by'],' ')"/>
                <xsl:if test="col[@field='Approved by']!=''">
                    <!-- Person record -->
                    <resource name="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$pr_Approver"/>
                        </xsl:attribute>
                        <data field="first_name">
                            <xsl:value-of select="$appFirstName"/>
                        </data>
                        <data field="last_name">
                            <xsl:value-of select="$appLastName"/>
                        </data>
                    </resource>
                    <!-- HR  Requester -->
                    <resource name="hrm_human_resource">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$hrm_Approver"/>
                        </xsl:attribute>
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$pr_Approver"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- ********************************************************** -->
                <!--  Requested for -->
                <!--  Person Record -->
                <xsl:variable name="pr_RequestFor"><xsl:value-of select="concat('pr_', col[@field='Requested for'])"/></xsl:variable>
                <xsl:variable name="hrm_RequestFor"><xsl:value-of select="concat('hrm_', col[@field='Requested for'])"/></xsl:variable>
                <xsl:variable name="rfFirstName"  select="substring-before(col[@field='Requested for'],' ')"/>
                <xsl:variable name="rfLastName"  select="substring-after(col[@field='Requested for'],' ')"/>
                <xsl:if test="col[@field='Requested for']!=''">
                    <!-- Person record -->
                    <resource name="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$pr_RequestFor"/>
                        </xsl:attribute>
                        <data field="first_name">
                            <xsl:value-of select="$rfFirstName"/>
                        </data>
                        <data field="last_name">
                            <xsl:value-of select="$rfLastName"/>
                        </data>
                    </resource>
                    <!-- HR  Requester -->
                    <resource name="hrm_human_resource">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$hrm_RequestFor"/>
                        </xsl:attribute>
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$pr_RequestFor"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- ********************************************************** -->
                <!--  Received by -->
                <!--  Person Record -->
                <xsl:variable name="pr_ReceivedBy"><xsl:value-of select="concat('pr_', col[@field='Received by'])"/></xsl:variable>
                <xsl:variable name="hrm_ReceivedBy"><xsl:value-of select="concat('hrm_', col[@field='Received by'])"/></xsl:variable>
                <xsl:variable name="recFirstName"  select="substring-before(col[@field='Received by'],' ')"/>
                <xsl:variable name="recLastName"  select="substring-after(col[@field='Received by'],' ')"/>
                <xsl:if test="col[@field='Received by']!=''">
                    <!-- Person record -->
                    <resource name="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$pr_ReceivedBy"/>
                        </xsl:attribute>
                        <data field="first_name">
                            <xsl:value-of select="$recFirstName"/>
                        </data>
                        <data field="last_name">
                            <xsl:value-of select="$recLastName"/>
                        </data>
                    </resource>
                    <!-- HR  Requester -->
                    <resource name="hrm_human_resource">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$hrm_ReceivedBy"/>
                        </xsl:attribute>
                        <reference field="person_id" resource="pr_person">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$pr_ReceivedBy"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- ********************************************************** -->
                <!-- Request -->
                <resource name="req_req">
                    <reference field="event_id" resource="event_event">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Event"/>
                        </xsl:attribute>
                    </reference>
                    <data field="req_ref"><xsl:value-of select="col[@field='Request Number']"/></data>
                    <data field="date"><xsl:value-of select="col[@field='Date Requested']"/></data>
                    <data field="time_requested"><xsl:value-of select="col[@field='Time Requested']"/></data>
                    <reference field="requester_id" resource="hrm_human_resource">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$hrm_Requester"/>
                        </xsl:attribute>
                    </reference>
                    <xsl:if test="col[@field='Assigned To']!=''">
                        <reference field="assigned_to_id" resource="hrm_human_resource">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$hrm_AssignedTo"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:if>
                    <xsl:choose>
                        <xsl:when test="col[@field='Priority']='Low'">
                            <data field="priority">1</data>
                        </xsl:when>
                        <xsl:when test="col[@field='Priority']='Medium'">
                            <data field="priority">2</data>
                        </xsl:when>
                        <xsl:when test="col[@field='Priority']='High'">
                            <data field="priority">3</data>
                        </xsl:when>
                        <xsl:otherwise>
                            <data field="priority">2</data>
                        </xsl:otherwise>
                    </xsl:choose>

                    <data field="purpose"><xsl:value-of select="col[@field='Purpose']"/></data>
                    <data field="date_required"><xsl:value-of select="col[@field='Date Required']"/></data>
                    <data field="time_required"><xsl:value-of select="col[@field='Time Required']"/></data>
                    <xsl:if test="col[@field='Requested for Facility']!=''">
                        <reference field="site_id" resource="inv_warehouse">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$Site"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:if>
                    <xsl:if test="col[@field='Approved by']!=''">
                        <reference field="approved_by_id" resource="hrm_human_resource">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$hrm_Approver"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:if>
                    <xsl:if test="col[@field='Requested for']!=''">
                        <reference field="request_for_id" resource="hrm_human_resource">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$hrm_RequestFor"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:if>
                    <xsl:if test="col[@field='Received by']!=''">
                        <reference field="recv_by_id" resource="hrm_human_resource">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$hrm_ReceivedBy"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:if>
                    <data field="transport_req"><xsl:value-of select="col[@field='Transportation Required']"/></data>
                    <data field="security_req"><xsl:value-of select="col[@field='Security Required']"/></data>
                    <data field="date_recv"><xsl:value-of select="col[@field='Date Delivered']"/></data>
                    <data field="time_recv"><xsl:value-of select="col[@field='Time Delivered']"/></data>
                    <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
                </resource>
            </xsl:for-each>
        </s3xml>
    </xsl:template>
</xsl:stylesheet>
