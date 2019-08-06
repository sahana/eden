# -*- coding: utf-8 -*-

from gluon import current, HTTP

from s3 import S3Method, s3_decode_iso_datetime, s3_str
from s3.codecs.xls import S3XLS
from s3compat import StringIO

# =============================================================================
class ResponsePerformanceIndicators(S3Method):
    """ REST Method to produce a response statistics data sheet """

    def __init__(self):
        """
            Constructor
        """

        self.styles = None

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}

        if r.http == "GET":
            if r.representation == "xls":
                output = self.xls(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def xls(self, r, **attr):
        """
            Export the performance indicators as XLS data sheet

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T
        s3db = current.s3db

        try:
            import xlwt
        except ImportError:
            raise HTTP(503, body="XLWT not installed")

        title = s3_str(T("Performance Indicators"))
        write = self.write

        # Create workbook and sheet
        book = xlwt.Workbook(encoding="utf-8")
        sheet = book.add_sheet(title)

        # Get the statistics
        resource = self.resource
        table = resource.table
        indicators = self.indicators(resource)

        # Title and Report Dates (from filter)
        write(sheet, 0, 0, title, style="header")
        dates = []
        get_vars = r.get_vars
        field = table.date
        for fvar in ("~.date__ge", "~.date__le"):
            dtstr = get_vars.get(fvar)
            if dtstr:
                try:
                    dt = s3_decode_iso_datetime(dtstr).date()
                except (ValueError, AttributeError):
                    dt = None
                else:
                    dates.append(field.represent(dt))
            else:
                dates.append("...")
        if dates:
            write(sheet, 1, 0, " -- ".join(dates))

        # Basic performance indicators
        rowindex = 3
        # Total number of consultations
        write(sheet, rowindex, 0, T("Total Number of Consultations"))
        write(sheet, rowindex, 1, indicators.get("total_responses", ""))

        rowindex += 1
        write(sheet, rowindex, 0, T("Total Number of Clients"))
        write(sheet, rowindex, 1, indicators.get("total_clients", ""))

        rowindex += 1
        write(sheet, rowindex, 0, T("Average Duration of Consultations (minutes)"))
        avg_hours_per_response = indicators.get("avg_hours_per_response")
        if avg_hours_per_response:
            avg_minutes_per_response = int(round(avg_hours_per_response * 60))
        else:
            avg_minutes_per_response = ""
        write(sheet, rowindex, 1, avg_minutes_per_response)

        rowindex += 1
        write(sheet, rowindex, 0, T("Average Number of Consultations per Client"))
        write(sheet, rowindex, 1, indicators.get("avg_responses_per_client", ""))

        # Distribution
        rowindex = 8
        write(sheet, rowindex, 0, T("Distribution of Clients"))

        write(sheet, rowindex, 1, T("Single"))
        write(sheet, rowindex, 2, indicators.get("singles", ""))

        rowindex += 1
        write(sheet, rowindex, 1, T("Family"))
        write(sheet, rowindex, 2, indicators.get("families", ""))

        rowindex += 1
        write(sheet, rowindex, 1, T("Group Counseling"))

        rowindex += 1
        write(sheet, rowindex, 1, T("Individual Counseling"))
        write(sheet, rowindex, 2, indicators.get("total_responses", ""))

        # Top-5's
        rowindex = 13
        write(sheet, rowindex, 0, T("Top 5 Countries of Origin"))
        top_5_nationalities = indicators.get("top_5_nationalities")
        if top_5_nationalities:
            dtable = s3db.pr_person_details
            field = dtable.nationality
            for rank, nationality in enumerate(top_5_nationalities):
                write(sheet, rowindex, 1, "%s - %s" % (rank + 1, field.represent(nationality)))
                rowindex += 1

        rowindex += 1
        write(sheet, rowindex, 0, T("Top 5 Counseling Reasons"))
        top_5_needs = indicators.get("top_5_needs")
        if top_5_needs:
            ttable = s3db.dvr_response_theme
            field = ttable.need_id
            for rank, need in enumerate(top_5_needs):
                write(sheet, rowindex, 1, "%s - %s" % (rank + 1, field.represent(need)))
                rowindex += 1

        # Output
        output = StringIO()
        book.save(output)
        output.seek(0)

        # Response headers
        from gluon.contenttype import contenttype
        disposition = "attachment; filename=\"%s\"" % "indicators.xls"
        response = current.response
        response.headers["Content-Type"] = contenttype(".xls")
        response.headers["Content-disposition"] = disposition

        from gluon.streamer import DEFAULT_CHUNK_SIZE
        return response.stream(output,
                               chunk_size=DEFAULT_CHUNK_SIZE,
                               request=r,
                               )

    # -------------------------------------------------------------------------
    def write(self, sheet, rowindex, colindex, label, style="odd"):
        """
            Write a label/value into the XLS worksheet

            @param sheet: the worksheet
            @param rowindex: the row index
            @param colindex: the column index
            @param label: the label/value to write
            @param style: style name (S3XLS styles)
        """

        styles = self.styles
        if not styles:
            self.styles = styles = S3XLS._styles()

        style = styles.get(style)
        if not style:
            import xlwt
            style = xlwt.XFStyle()

        label = s3_str(label)

        # Adjust column width
        col = sheet.col(colindex)
        curwidth = col.width or 0
        adjwidth = max(len(label) * 240, 2480) if label else 2480
        col.width = max(curwidth, adjwidth)

        row = sheet.row(rowindex)
        row.write(colindex, label, style)

    # -------------------------------------------------------------------------
    def indicators(self, resource):
        """
            Query/compute the performance indicators

            @param resource: the filtered dvr_response_action resource

            @returns: dict with performance indicators (raw values)
        """

        db = current.db
        s3db = current.s3db

        table = resource.table
        rows = resource.select(["id"], as_rows=True)

        # Master query
        record_ids = set(row.id for row in rows)
        master_query = table._id.belongs(record_ids)

        # Total responses
        total_responses = len(record_ids)

        # Total clients, average effort per response
        num_clients = table.person_id.count(distinct=True)
        avg_hours = table.hours.avg()

        row = db(master_query).select(num_clients,
                                      avg_hours,
                                      ).first()
        total_clients = row[num_clients]
        avg_hours_per_response = row[avg_hours]

        # Average number of responses per client
        if total_clients:
            avg_responses_per_client = total_responses / total_clients
        else:
            avg_responses_per_client = 0

        # Number of clients without family members in case group
        ctable = s3db.dvr_case
        join = ctable.on((ctable.person_id == table.person_id) & \
                         (ctable.household_size == 1))

        num_clients = table.person_id.count(distinct=True)

        row = db(master_query).select(num_clients,
                                      join = join,
                                      ).first()
        singles = row[num_clients]
        families = total_clients - singles

        # Top 5 Nationalities
        dtable = s3db.pr_person_details
        left = dtable.on(dtable.person_id == table.person_id)

        nationality = dtable.nationality
        num_clients = table.person_id.count(distinct=True)

        rows = db(master_query).select(nationality,
                                       groupby = nationality,
                                       orderby = ~num_clients,
                                       left = left,
                                       limitby = (0, 5),
                                       )
        top_5_nationalities = [row[nationality] for row in rows]

        # Top 5 Needs (only possible if using themes+needs)
        if current.deployment_settings.get_dvr_response_themes_needs():

            ltable = s3db.dvr_response_action_theme
            ttable = s3db.dvr_response_theme
            left = ttable.on(ttable.id == ltable.theme_id)

            num_responses = ltable.action_id.count(distinct=True)
            need = ttable.need_id

            query = ltable.action_id.belongs(record_ids)
            rows = db(query).select(need,
                                    groupby = need,
                                    orderby = ~num_responses,
                                    left = left,
                                    limitby = (0, 5),
                                    )
            top_5_needs = [row[need] for row in rows]
        else:
            top_5_needs = None

        # Return indicators
        return {"total_responses": total_responses,
                "total_clients": total_clients,
                "avg_hours_per_response": avg_hours_per_response,
                "avg_responses_per_client": avg_responses_per_client,
                "top_5_nationalities": top_5_nationalities,
                "top_5_needs": top_5_needs,
                "singles": singles,
                "families": families,
                }

# END =========================================================================
