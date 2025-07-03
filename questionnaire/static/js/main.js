// Enable Bootstrap form validation
(function () {
    'use strict'
    
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    const forms = document.querySelectorAll('.needs-validation')
    
    // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            
            form.classList.add('was-validated')
        }, false)
    })
})();

// Auto-format mobile number
document.addEventListener('DOMContentLoaded', function() {
    const mobileField = document.getElementById('id_mobile_number');
    if (mobileField) {
        mobileField.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) value = value.substring(0, 10);
            e.target.value = value;
        });
    }
});