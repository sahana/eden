# -*- coding: utf-8 -*-

import os

from gluon import *
#from gluon.storage import Storage
#from s3 import *

# =============================================================================
def INPUT_BTN(**attributes):
    return SPAN(INPUT(_class = "button-right",
                      **attributes), 
                _class = "button-left")

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        T = current.T
        request = current.request
        response = current.response
        appname = request.application

        path = os.path.join(current.request.folder, "private", "templates",
                            response.s3.theme, "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(path, "rb")
        except IOError:
            raise HTTP("404", "Unable to open Custom View: %s" % path)

        home_img = IMG(_src="/%s/static/themes/DRRPP/img/home_img.jpg" % appname,
                       _id="home_img")
        home_page_img = IMG(_src="/%s/static/themes/DRRPP/img/home_page_img.png" % appname,
                            _id="home_page_img")
        home_map_img = IMG(_src="/%s/static/themes/DRRPP/img/home_map_img.png" % appname,
                           _id="home_map_img")

        list_img = A(IMG(_src="/%s/static/themes/DRRPP/img/list_img.png" % appname,
                         _id="list_img"),
                     _href=URL(c="project", f="project", args=["list"]),
                     _title="Project List")
        
        matrix_img = A(IMG(_src="/%s/static/themes/DRRPP/img/matrix_img.png" % appname,
                           _id="matrix_img"),
                       _href=URL(c="project", f="project", args=["matrix"]),
                       _title="Project Matrix Report")
        
        map_img = A(IMG(_src="/%s/static/themes/DRRPP/img/map_img.png" % appname,
                        _id="map_img"),
                    _href=URL( f="project", args=["map"]),
                    _title="Project Map")
        
        graph_img = A(IMG(_src="/%s/static/themes/DRRPP/img/graph_img.png" % appname,
                          _id="graph_img"),
                      _href=URL(c="project", f="project", args=["graphs"]),
                      _title="Project Graph")

        add_pipeline_project_link = URL(c="project",
                                        f="project",
                                        args=["create"],
                                        vars=dict(set_status_id = "1"))    
        add_current_project_link = URL(c="project", 
                                       f="project",
                                       args=["create"],
                                       vars=dict(set_status_id = "2"))
        add_completed_project_link = URL(c="project", 
                                         f="project",
                                         args=["create"],
                                         vars=dict(set_status_id = "3"))
        add_offline_project_link = URL(c="static",
                                       f="DRR_Project_Portal_New_Project_Form.doc")
        
        add_framework_link = URL(c="project", 
                                 f="framework",
                                 args=["create"])
        
        project_captions = {
            1:"DRR projects which will be being implemented in the future, and for which funding has been secured in the Asia and Pacific region.",
            2:"DRR projects which are currently being implemented in one or more country in the Asia and Pacific region.",
            3:"DRR projects which have been completed and are no longer being implemented in the Asia and Pacific region."
            }
        framework_caption = "Frameworks, action plans, road maps, strategies, declarations, statements and action agendas on DRR or DRR related themes, which are documents or instruments for guiding stakeholders on DRR planning, programming and implementation."
        add_div = DIV(A(DIV("ADD ", SPAN("CURRENT", _class="white_text"), " PROJECT"),
                        _href=add_current_project_link,
                        _title=project_captions[2]),
                      A(DIV("ADD ", SPAN("PROPOSED", _class="white_text"), " PROJECT" ),
                        _href=add_pipeline_project_link,
                        _title=project_captions[1]),                       
                      A(DIV("ADD ", SPAN("COMPLETED", _class="white_text"), " PROJECT" ), 
                        _href=add_completed_project_link,
                        _title=project_captions[3]),
                      A(DIV("ADD PROJECT OFFLINE" ),
                        _href=add_offline_project_link,
                        _title="Download a form to enter a DRR projects off-line and submit by Email"),
                      A(DIV("ADD ", SPAN("DRR FRAMEWORK", _class="white_text")),
                        _href=add_framework_link,
                        _title=framework_caption),
                      _id="add_div"
                     )

        why_box = DIV(H1("WHY THIS PORTAL?"),
                      UL("Share information on implementation of DRR: Who? What? Where?",
                         "Collectively identify gaps, improve planning and programming on DRR",
                         "Identify areas of cooperation on implementation of DRR"
                         ),
                      _id="why_box")

        what_box = DIV(H1("WHAT CAN WE GET FROM THIS PORTAL?"),
                       UL("List of completed and ongoing DRR projects - by country, hazards, themes, partners and donors.",
                          "List of planned/proposed projects - better planning of future projects.",
                          "Quick analysis - on number and types of completed and ongoing DRR projects", 
                          "Generate customised graphs and maps.",
                          "Know more on the DRR frameworks/action plans guiding the region - identify priority areas for providing support and implementation.",
                          "List of organisations implementing DRR projects at regional level.",
                          "Archive of periodic meetings of regional DRR mechanisms."
                          ),
                       _id="what_box")

        how_help_box = DIV(H1("HOW WOULD THIS INFORMATION HELP?"),
                           H2("National Government"),
                           UL("Gain clarity on types of support that may be accessed from regional level and thus receive coherent regional assistance"),
                           H2("Organisation Implementing DRR Projects"),
                           UL("Plan better-knowing who does what, and where; Find partners and scale up implementation; and Learn from past and ongoing work of partners"),
                           H2("Donor Agencies"),
                           UL("Identify priorities to match your policy and programmatic imperatives; and minimise overlap; maximise resources"),
                           _id="how_help_box")

        how_start_box = DIV(H1("HOW DO WE GET STARTED?"),
                            UL("Add information on  current / proposed / completed DRR projects",
                               "Search for information - project list, project analysis, DRR frameworks",
                               "Log in to add and edit your data",
                               "Link to this portal from your organisation website"
                               ),
                            _id="how_start_box")    
        
        help = A(DIV("USER MANUAL",
                     _id="help_div"),
                 _href=URL(c="static", f="DRR_Portal_User_Manual.pdf"),
                 _target="_blank"
                 )   
        
        tour = A(DIV("VIDEO TOUR",
                     _id="tour_div"),
                 _href=URL(c="default", f="index", args="video"),
                 _target="_blank"
                 )

        db = current.db
        s3db = current.s3db
        table = s3db.project_project
        query = (table.deleted == False)
        #approved = & (table.approved == True)
        #current = & (table.status_id == 2)
        #proposed = & (table.status_id == 1)
        #completed = & (table.status_id == 1)
        projects = db(query).count()
        ftable = s3db.project_framework
        query = (ftable.deleted == False)
        #approved = & (table.approved == True)
        frameworks = db(query).count()
        stats = DIV(DIV("Currently the DRR Projects Portal has information on:"),
                    TABLE(TR(projects,
                             A("Projects",
                               _href=URL(c="project", f="project",
                                         args=["list"]))
                             ),
                          TR(TD(),
                             TABLE(TR(projects,
                                      A("Current Projects",
                                        _href=URL(c="project", f="project",
                                                  args=["list"],
                                                  vars={"status_id":2}))
                                     )
                                   )
                             ),
                          TR(TD(),
                             TABLE(TR(projects,
                                      A("Proposed Projects",
                                        _href=URL(c="project", f="project",
                                                  args=["list"],
                                                  vars={"status_id":1}))
                                     )
                                    )
                             ),   
                          TR(TD(),
                             TABLE(TR(projects,
                                      A("Completed Projects",
                                        _href=URL(c="project", f="project",
                                                  args=["list"],
                                                  vars={"status_id":3}))
                                     )
                                    )
                             ),   
                          TR(frameworks,
                             A("Frameworks",
                               _href=URL(c="project", f="framework"))
                            ),                                                                                                              
                         ),
                    _id="stats_div")
        
        market = DIV(DIV(I("Under Development...")),
                     H2("DRR Project Marketplace"),
                     DIV("A platform to coordinate and collaborate on future DRR Projects."),
                     _id = "market_div")  
        
        auth = current.auth
        _table_user = auth.settings.table_user
        _table_user.language.label = T("Language")
        _table_user.language.default = "en"
        _table_user.language.comment = DIV(_class="tooltip",
                                           _title=T("Language|The language to use for notifications."))
        #_table_user.language.requires = IS_IN_SET(s3_languages)
        languages = current.deployment_settings.get_L10n_languages()
        _table_user.language.represent = lambda opt: \
            languages.get(opt, current.messages.UNKNOWN_OPT)  

        request.args = ["login"]
        login = auth()
        login[0][-1][1][0] = INPUT_BTN(_type = "submit",
                                      _value = T("Login"))

        return dict(title = T("Home"),
                    home_img = home_img,                
                    add_div = add_div, 
                    login = login,
                    why_box = why_box,
                    home_page_img = home_page_img,
                    what_box = what_box,
                    how_help_box = how_help_box,
                    home_map_img = home_map_img,
                    how_start_box = how_start_box,
                    tour = tour,
                    help = help,
                    stats = stats, 
                    market = market,
                    list_img = list_img,
                    matrix_img = matrix_img,
                    map_img = map_img,
                    graph_img = graph_img,
                    )

# END =========================================================================
