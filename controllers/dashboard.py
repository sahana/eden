import s3chart.py,datetime
from s3 import *


def index():
    
    db = current.db
    
    # table names
    voltable = s3db.vol_details
    hrmtable = s3db.hrm_human_resource
    pr_gender_opts = s3db.pr_gender_opts
    pr_age_group_opts = s3db.pr_age_group_opts
    table = s3db.pr_person
    etable = s3db.pr_contact
    reqtable = s3db.req_req
    projtable = s3db.project_project
    orgtable = s3db.org_organisation
    eventtable = s3db.event_event
    
    req_type_opts = {1 : "Warehouse stock", 3: "People" , 9 : "Others"}
    
    # lists for returning values to index.html
    gender = [0,0,0]
    contacts = []
    now = S3DateTime()
    three_months_prior = current.request.utcnow - datetime.timedelta(days=92)
    active = s3db.vol_active
    reqs = []
    projs = []
    events = []
    
    #----------------------------------------------------------------------------
    # volunteer info : pie chart , contact info
    
    row2 = db(voltable.deleted==False).count()
    row1 = db((hrmtable.type == 2) & (hrmtable.deleted==False)).select(hrmtable.person_id,hrmtable.end_date)
    c = db((hrmtable.type == 2) & (hrmtable.deleted==False)).count() or 1
    
   
    for r in row1 :
        query = (table.id == r.person_id)
        x = db(query).select(table.gender,table.first_name)
        if r.end_date < now :
            
            query1 = (r.person_id == etable.pe_id) & (etable.deleted==False)
            email = db(query).select(etable.value).first()
            contacts.append(x[0].first_name+"#"+email.value)
        gender[x[0].gender - 1]+=1
   
   #----------------------------------------------------------------------------
   
   # request info 
   
    query = (reqtable.closed==False)&(reqtable.deleted==False)
    row = db(query).select(reqtable.date_required,reqtable.priority,reqtable.requester_id,reqtable.type)
    for r in row :
       req = []
       req.append(str(r.date_required))
       req.append(r.priority)
       sub_query = (table.id == reqtable.requester_id)&(table.deleted==False)
       name = db(query).select(table.first_name).first()
       name = name.first_name
       req.append(name)
       req.append(req_type_opts[r.type])
       reqs.append(req)
       
    #---------------------------------------------------------------------------
    
    #project info 
    
    query = (projtable.deleted==False)& (projtable.end_date < now) #&(projtable.status_id !=)
    row = db(query).select(projtable.organisation_id,projtable.status_id,projtable.name)
    for r in row :
        proj = []
        proj.append(r.name)
        proj.append(projtable.status_id.represent(r.status_id))
        subquery = (orgtable.id == r.organisation_id) & (orgtable.deleted==False)
        name = db(query).select(orgtable.name).first()
        name = name.name
        proj.append(name)
        projs.append(proj)
    
    
    
    #---------------------------------------------------------------------------
    #event info
    
    query = (eventtable.zero_hour > three_months_prior) &(eventtable.deleted==False)
    row = db(query).select(eventtable.name,eventtable.zero_hour)
    for r in row :
        event = []
        event.append(r.name)
        event.append(r.zero_hour)
        events.append(event)
    
    
    
    
    
    # chart ---------------------------------------------------------------------
    
    chart = s3chart.S3Chart(path="samplechart",width=4,height = 3)

    fracs = [30,40,30]
    lables = ['unspec.','female','male']

    chart.dashPie('volunteers',gender,lables)
    img  = chart.draw()
   
    return dict(img = img,c=contacts,reqs = reqs,projs = projs,events=events)