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
});
