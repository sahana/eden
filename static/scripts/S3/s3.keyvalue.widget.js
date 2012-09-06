(function ($, undefined) {
    $.fn.kv_pairs = function (key_label, value_label) {
        var $self = $(this),
            $list = $('<ul></ul>'),
            id = $(this).attr('id');

        try {
            var kvs = $.parseJSON($(this).val());
        } catch (e) {
            s3_debug('There was an error parsing json for key value widget.', e);
            return;
        }

        if ($(this).data('kvp-loaded')) return;
        $(this).hide();
        key_label = ' ' + key_label + ': '
        value_label = ' ' + value_label + ': '
        $more = $('<a>+</a>').css('cursor', 'pointer').click(cleanup);

        // handler util
        function cleanup() {
            kvs = [];
            $list.find('li').each(function () {
                var k = $(this).find('.key').eq(0).val(),
                    v = $(this).find('.value').eq(0).val();

                if (k == '' && v == '') $(this).remove();
                else kvs[kvs.length] = {key: k, value: v}
            });

            var $item = $('<li></li>'),
                $key = $('<input class="key" value="" />'),
                $value = $('<input class="value" value="" />');

            $value.blur(cleanup);

            $item.append(key_label, $key, value_label, $value, ' ', $more);
            $list.append($item);

            $key.focus();
            $self.html(JSON.stringify(kvs));
        }

        for (var i=0, len=kvs.length; i < len; i++) {
            if (!kvs[i]) continue;

            var item = kvs[i],
                ops = item && item.options,
                immutable = Number(item.immutable),
                $item = $('<li></li>').attr('id', id + '-' + i),
                $key = $('<input class="key" value="' + (item.key || '') + '" />'),
                $value = $('<input class="value" value="' + (item.value || '') + '" />');

            if (immutable) {
                if (immutable & 1) {
                    $key.attr('disabled', true);
                }
                if (immutable & 2) {
                    $value.attr('disabled', true);
                }
            }

            if (typeof(ops) == 'object') {
                $value = $('<select class="value generic-widget"></select>');
                for (var j=0, len=ops.length; j < len; j++) {
                    $value.append($('<option value="' + ops[j][0] + '">' + ops[j][1] + '</options>'));
                }
            }

            var $help = '';
            if (typeof(item.comment) == 'string') {
                $help = $('<span class="kv-help" style="float:right"></span>').text(item.comment);
            }

            $value.blur(cleanup);

            $item.append(key_label, $key, value_label, $value, ' ', $more, ' ', $help);
            $list.append($item);
        }

        cleanup();

        $(this).after($list);

    }
})(jQuery);
