# -*- coding: utf-8 -*-

"""
    REST Method to produce a PDF of HR records to collect signatures

    @copyright: 2018 (c) Sahana Software Foundation
    @license: MIT

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
"""

__all__ = ("HRSignatureList")

import os

from gluon import current, DIV, H4, H5, IMG, TABLE, TD, TH, TR
from gluon.contenttype import contenttype

from s3 import S3Method, s3_format_fullname
from s3.codecs.pdf import EdenDocTemplate, S3RL_PDF

# =============================================================================
class HRSignatureList(S3Method):
    """ REST Method to produce a PDF of HR records to collect signatures """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}

        if r.http == "GET":
            if r.representation == "pdf":
                output = self.pdf(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def extract(self, resource):
        """
            Extract the HR records

            @param resource: the hrm_human_resource resource

            @returns: tuple (data, pictures), where
                      - data is a S3ResourceData instance
                      - pictures is a dict {pe_id: filepath}
        """

        db = current.db
        s3db = current.s3db

        list_fields = ["id",
                       "code",
                       "person_id$pe_id",
                       "person_id$first_name",
                       "person_id$middle_name",
                       "person_id$last_name",
                       "person_id$national_id.value",
                       "organisation_id",
                       "programme_hours.programme_id",
                       ]

        orderby = resource.get_config("orderby")
        if orderby is None:
            orderby = resource._id

        data = resource.select(list_fields,
                               represent = True,
                               show_links = False,
                               raw_data = True,
                               orderby = orderby,
                               )

        # Get all PE IDs
        pe_ids = set(row["_row"]["pr_person.pe_id"] for row in data.rows)

        # Look up all profile pictures
        itable = s3db.pr_image
        query = (itable.pe_id.belongs(pe_ids)) & \
                (itable.profile == True) & \
                (itable.deleted == False)
        rows = db(query).select(itable.pe_id, itable.image)

        field = itable.image
        if field.uploadfolder:
            path = field.uploadfolder
        else:
            path = os.path.join(current.request.folder, 'uploads')

        pictures = {row.pe_id: os.path.join(path, row.image)
                    for row in rows if row.image
                    }

        return data, pictures

    # -------------------------------------------------------------------------
    @staticmethod
    def get_report_organisation(r):
        """
            Identify the report organisation

            @param r: the S3Request

            @returns: a tuple (organisation_id, label)
        """

        db = current.db
        s3db = current.s3db

        organisation_id, label = None, None

        # Introspect the organisation filter first
        orgfilter = r.get_vars.get("~.organisation_id__belongs")
        if orgfilter:
            org_ids = orgfilter.split(",")
            if not org_ids:
                organisation_id = None
            elif len(org_ids) == 1:
                # Filtered to a single organisation
                try:
                    organisation_id = long(org_ids[0])
                except (ValueError, TypeError):
                    pass
            else:
                # Do all filter-orgs belong to the same NS?
                otable = s3db.org_organisation
                query = (otable.id.belongs(org_ids)) & \
                        (otable.deleted == False)
                try:
                    rows = db(query).select(otable.root_organisation,
                                            groupby = otable.root_organisation,
                                            )
                except (ValueError, TypeError):
                    pass
                else:
                    if len(rows) == 1:
                        organisation_id = rows.first().root_organisation

        if organisation_id is None:
            # Can the user see records of only one NS anyway?
            realms = current.auth.permission.permitted_realms("hrm_human_resource", "read")
            if realms:
                otable = s3db.org_organisation
                query = (otable.pe_id.belongs(realms)) & \
                        (otable.deleted == False)
                rows = db(query).select(otable.root_organisation,
                                        groupby = otable.root_organisation,
                                        )
                if len(rows) == 1:
                    organisation_id = rows.first().root_organisation

        if organisation_id:
            # Represent the organisation_id
            field = r.table.organisation_id
            label = field.represent(organisation_id)

        return organisation_id, label

    # -------------------------------------------------------------------------
    @staticmethod
    def get_report_programme(r):
        """
            Identify the report programme

            @param r: the S3Request

            @returns: a tuple (programme_id, label)
        """

        programme_id, label = None, None

        # Introspect the programme filter
        progfilter = r.get_vars.get("person_id$hours.programme_id__belongs") or \
                     r.get_vars.get("~.person_id$hours.programme_id__belongs")
        if progfilter:
            prog_ids = progfilter.split(",")
            if len(prog_ids) == 1:
                try:
                    programme_id = long(prog_ids[0])
                except (ValueError, TypeError):
                    pass

        if programme_id:
            table = current.s3db.hrm_programme_hours
            field = table.programme_id
            label = current.T("Programme: %(programme)s") % \
                        {"programme": field.represent(programme_id)}

        return programme_id, label

    # -------------------------------------------------------------------------
    def pdf(self, r, **attr):
        """
            Generate the PDF

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        T = current.T

        db = current.db
        s3db = current.s3db

        # Look up the report organisation
        logo = None
        org_id, org_label = self.get_report_organisation(r)
        if org_id:
            # Look up the root organisation's logo
            otable = s3db.org_organisation
            rotable = otable.with_alias("root_organisation")
            join = rotable.on(rotable.id == otable.root_organisation)
            field = rotable.logo
            row = db(otable.id == org_id).select(field,
                                                 join = join,
                                                 limitby = (0, 1),
                                                 ).first()
            if row and row.logo:
                if field.uploadfolder:
                    path = field.uploadfolder
                else:
                    path = os.path.join(current.request.folder, 'uploads')
                logo = os.path.join(path, row.logo)

        # Look up the report programme
        prog_id, prog_label = self.get_report_programme(r)

        # Extract the HR records
        data, pictures = self.extract(r.resource)

        # Construct the header
        title = T("Official Volunteer List")
        header = TABLE(_class = "no-grid",
                       )
        trow = TR()
        if logo:
            trow.append(TD(IMG(_src=logo, _width="80"),
                           _rowspan = 3 if prog_id else 2,
                           ))
        trow.append(TD(H4(title), _colspan = 3))
        header.append(trow)
        if org_id:
            header.append(TR(TD(H5(org_label), _colspan = 3)))
        if prog_id:
            header.append(TR(TD(prog_label, _colspan = 3)))
        header.append(TR(TD()))

        # Should we show the branch column?
        branches = set(row["_row"]["hrm_human_resource.organisation_id"] for row in data.rows)
        if org_id:
            show_branch = len(branches) > 1
            org_repr = s3db.org_OrganisationRepresent(show_link = False,
                                                      parent = False,
                                                      acronym = True,
                                                      )
        else:
            show_branch = True
            org_repr = r.table.organisation_id.represent
        org_repr.bulk(list(branches))

        # Construct the table header
        labels = TR(TH(T("Picture")),
                    TH(T("Name")),
                    TH(T("Last Name")),
                    TH(T("National ID")),
                    TH(T("Volunteer ID")),
                    TH(T("Signature")),
                    )
        if show_branch:
            labels.insert(1, TH(T("Branch")))
        if not prog_id:
            labels.insert(2, TH(T("Programme")))

        # Build the table
        body = TABLE(labels, _class="repeat-header")

        # Add the data rows
        for row in data.rows:

            raw = row._row

            # Picture
            picture = pictures.get(raw["pr_person.pe_id"])
            if picture:
                picture = IMG(_src=picture,
                              _width=80,
                              )
            else:
                picture = ""

            # Name
            name = s3_format_fullname(fname = raw["pr_person.first_name"],
                                      mname = raw["pr_person.middle_name"],
                                      lname = "",
                                      truncate = False,
                                      )

            # Build the row
            trow = TR(TD(picture),
                      TD(name),
                      TD(row["pr_person.last_name"]),
                      TD(row["pr_national_id_identity.value"]),
                      TD(row["hrm_human_resource.code"]),
                      TD(),
                      )
            if show_branch:
                trow.insert(1, TD(org_repr(raw["hrm_human_resource.organisation_id"])))
            if not prog_id:
                trow.insert(2, TD(row["hrm_programme_hours.programme_id"]))
            body.append(trow)

        footer = DIV()

        doc = EdenDocTemplate(title=title)
        printable_width = doc.printable_width

        get_html_flowable = S3RL_PDF().get_html_flowable

        header_flowable = get_html_flowable(header, printable_width)
        body_flowable = get_html_flowable(body, printable_width)
        footer_flowable = get_html_flowable(footer, printable_width)

        # Build the PDF
        doc.build(header_flowable,
                  body_flowable,
                  footer_flowable,
                  )
        filename = "siglist.pdf"

        # Return the generated PDF
        response = current.response
        response.headers["Content-Type"] = contenttype(".pdf")
        disposition = "attachment; filename=\"%s\"" % filename
        response.headers["Content-disposition"] = disposition

        return doc.output.getvalue()

# END =========================================================================
