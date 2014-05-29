require(['converse'], function (converse) {
    converse.initialize({
        allow_otr: true,
        auto_list_rooms: true,
        auto_subscribe: false,
        bosh_service_url: S3.chat_url,
        debug: true ,
        hide_muc_server: false,
        // @ToDo: Support other locales
        i18n: locales['en'],
        prebind: false,
        show_controlbox_by_default: true,
        xhr_user_search: false
    });
});

