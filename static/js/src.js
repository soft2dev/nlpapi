
$(document).ready(function() {  
    $('#btn_submit').click(function(){
        var url = '/api/nl-process';
        var data = {
            code: $('#textarea_code').val(),
        };
        console.log('data');
        console.log(data);
        axios.post(url, data, {
            headers: {
            'Content-Type': 'application/json',
            }
        })
        .then(function (response) {
            console.log('result');
            $('#words_number').text(response.data.numbers + " characters")
            $('#words').text(response.data.words)
            myJSON = JSON.stringify(response.data.json);
            console.log('json')
            console.log(myJSON)
            $('#textjson').text(myJSON)
        })
        .catch(function (error) {
            alert('oops');
            console.log(error);
        });  
    })
})
