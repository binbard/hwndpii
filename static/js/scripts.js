$(document).ready(function () {
    var activeTab = "{{ active_tab }}";
    if (activeTab === "csv") {
        $('#csv-tab').tab('show');
    } else {
        $('#text-tab').tab('show');
    }

    $('form').on('submit', function () {
        $('#loading').show();
    });

    bsCustomFileInput.init();

    $('#csvFile').on('change', function () {
        var fileName = $(this).val().split('\\').pop();
        $(this).next('.custom-file-label').html(fileName);
    });

    $('#textMode').on('change', function () {
        var selectedMode = $(this).val();
        if (selectedMode === 'encrypt' || selectedMode === 'decrypt') {
            $('#textKeyField').show();
        } else {
            $('#textKeyField').hide();
        }
    });

    $('#csvMode').on('change', function () {
        var selectedMode = $(this).val();
        if (selectedMode === 'encrypt' || selectedMode === 'decrypt') {
            $('#csvKeyField').show();
        } else {
            $('#csvKeyField').hide();
        }
    });

    var clipboard = new ClipboardJS('.copy-btn');

    clipboard.on('success', function(e) {
        $(e.trigger).attr('title', 'Copied!').tooltip('show');
        setTimeout(function() {
            $(e.trigger).attr('title', 'Copy to clipboard').tooltip('dispose');
        }, 2000);
        e.clearSelection();
    });

    clipboard.on('error', function(e) {
        alert('Failed to copy text.');
    });

    $('.copy-btn').tooltip({
        trigger: 'hover',
        placement: 'top'
    });
});
