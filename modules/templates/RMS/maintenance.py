# -*- coding: utf-8 -*-

import datetime
import os
import time

from gluon import current, URL
from gluon.settings import global_settings

from s3 import s3_str, S3DateTime
from .controllers import inv_operators_for_sites

# =============================================================================
class Daily():
    """ Daily Maintenance Tasks """

    def __call__(self):

        db = current.db
        s3db = current.s3db
        request = current.request

        now = request.utcnow
        month_past = now - datetime.timedelta(weeks = 4)

        # Cleanup Scheduler logs
        table = s3db.scheduler_run
        db(table.start_time < month_past).delete()

        # Cleanup Sync logs
        table = s3db.sync_log
        db(table.timestmp < month_past).delete()

        # Cleanup Sessions
        osjoin = os.path.join
        osstat = os.stat
        osremove = os.remove
        folder = osjoin(global_settings.applications_parent,
                        request.folder,
                        "sessions")
        # Convert to UNIX time
        month_past_u = time.mktime(month_past.timetuple())
        for file in os.listdir(folder):
            filepath = osjoin(folder, file)
            status = osstat(filepath)
            if status.st_mtime < month_past_u:
                try:
                    osremove(filepath)
                except:
                    pass

        # Cleanup Uploaded Import Spreadsheets
        week_past = now - datetime.timedelta(weeks = 1)

        from s3.s3import import S3Importer
        S3Importer.define_upload_table()

        table = s3db.s3_import_upload
        db(table.created_on < week_past).delete()

        # Check for Expiring Stock
        # @ToDo: Do we need to remove alerts?
        # - currently think that doesn't happen automatically
        ninety_days = now + datetime.timedelta(days = 90)
        table = s3db.inv_inv_item
        rows = db(table.expiry_date < ninety_days).select(table.id,
                                                          table.site_id,
                                                          table.item_id,
                                                          table.expiry_date,
                                                          table.quantity,
                                                          table.layout_id,
                                                          )
        if len(rows):

            ntable = s3db.auth_user_notification
            nquery = (ntable.tablename == "inv_inv_item")

            alerts = []

            for row in rows:
                record_id = row.id
                # Add Alert, if there is not one already present
                query = nquery & (ntable.record_id == record_id) & \
                                 (ntable.deleted == False)
                exists = current.db(query).select(table.id,
                                                  limitby = (0, 1)
                                                  ).first()
                if not exists:
                    alerts.append((record_id, row.site_id, row.item_id, row.expiry_date, row.quantity, row.layout_id))         

            if alerts:
                T = current.T
                session_s3 = current.session.s3
                ui_language = session_s3.language

                site_ids = [alert[1] for alert in alerts]

                # Lookup Site Operators
                sites = inv_operators_for_sites(site_ids)

                # Bulk Represent Items
                # - assumes that we are not using translate = True!
                item_ids = [alert[2] for alert in alerts]
                items = table.item_id.represent.bulk(item_ids, show_link=False)

                # Bulk Represent Bins
                layout_ids = [alert[5] for alert in alerts]
                bins = table.layout_id.represent.bulk(layout_ids)

                date_represent = S3DateTime.date_represent # We don't want to highlight in red!
                send_email = current.msg.send_by_pe_id
                subject_T = T("%(quantity)s %(item)s in %(bin)s from %(site)s Warehouse will expire on %(date)s")
                message_T = T("%(quantity)s %(item)s in %(bin)s from %(site)s Warehouse will expire on %(date)s. Please review at: %(url)s")
                alert_T = T("%(quantity)s %(item)s in %(bin)s from %(site)s Warehouse will expire on %(date)s")

                insert = ntable.insert

                for alert in alerts:
                    record_id = alert[0]
                    url = "%s%s" % (current.deployment_settings.get_base_public_url(),
                                    URL(c="inv", f="inv_item",
                                        args = record_id,
                                        ))
                    site = sites[alert[1]]
                    site_name = site["name"]
                    item = items.get(alert[2])
                    expiry_date = alert[3]
                    quantity = alert[4]
                    bin = bins.get(alert[5])

                    # Send Localised Alerts & Mail(s)
                    languages = {}
                    operators = site["operators"]
                    for row in operators:
                        language = row["auth_user.language"]
                        if language not in languages:
                            languages[language] = []
                        languages[language].append((row["pr_person_user.pe_id"], row["pr_person_user.user_id"]))
                    for language in languages:
                        T.force(language)
                        session_s3.language = language # for date_represent
                        date = date_represent(expiry_date)
                        subject = s3_str(subject_T) % {"quantity": quantity,
                                                       "item": item,
                                                       "bin": bin,
                                                       "site": site_name,
                                                       "date": date,
                                                       }
                        message = s3_str(message_T) % {"quantity": quantity,
                                                       "item": item,
                                                       "bin": bin,
                                                       "site": site_name,
                                                       "date": date,
                                                       "url": url,
                                                       }
                        alert = s3_str(alert_T) % {"quantity": quantity,
                                                   "item": item,
                                                   "bin": bin,
                                                   "site": site_name,
                                                   "date": date,
                                                   }

                        users = languages[language]
                        for user in users:
                            send_email(user[0],
                                       subject = subject,
                                       message = message,
                                       )
                            insert(user_id = user[1],
                                   name = alert,
                                   url = url,
                                   type = "expiry",
                                   tablename = "inv_inv_item",
                                   record_id = record_id,
                                   )

                # Restore language for UI
                session_s3.language = ui_language
                T.force(ui_language)

# END =========================================================================
