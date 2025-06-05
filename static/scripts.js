$(document).ready(function () {
    // Show toasts on page load
    $('.toast').toast({ delay: 5000 });
    $('.toast').toast('show');

    // Dark mode toggle
    $('#theme-toggle').click(function () {
        $('body').toggleClass('dark-mode');
        const isDark = $('body').hasClass('dark-mode');
        $(this).text(isDark ? 'Toggle Light Mode' : 'Toggle Dark Mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // Load saved theme
    if (localStorage.getItem('theme') === 'dark') {
        $('body').addClass('dark-mode');
        $('#theme-toggle').text('Toggle Light Mode');
    }

    // Show loading animation on form submission
    $('#generate-form, #save-form, #set-password-form').on('submit', function () {
        $('#loading-animation').show();
    });
});

function start2FARefresh(secretKey, uid = '') {
    function updateCode() {
        $('#loading-animation').show();
        $.ajax({
            url: '/get_2fa_code',
            method: 'POST',
            data: { secret_key: secretKey },
            success: function (data) {
                $('#loading-animation').hide();
                if (data.error) {
                    $('.toast-container').append(
                        `<div class="toast animate__slideInRight align-items-center text-white bg-error border-0" role="alert" aria-live="assertive" aria-atomic="true">
                            <div class="d-flex">
                                <div class="toast-body">${data.error}</div>
                                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                            </div>
                        </div>`
                    );
                    $('.toast').toast({ delay: 5000 });
                    $('.toast').toast('show');
                    return;
                }
                $('#current-code').text(data.code).addClass('animate__animated animate__pulse');
                $('#remaining-time').text(data.remaining);
                $('#progress-bar').css('width', (data.remaining / 30 * 100) + '%');
                setTimeout(() => $('#current-code').removeClass('animate__animated animate__pulse'), 500);
                setTimeout(updateCode, 1000);
            },
            error: function () {
                $('#loading-animation').hide();
                $('.toast-container').append(
                    `<div class="toast animate__slideInRight align-items-center text-white bg-error border-0" role="alert" aria-live="assertive" aria-atomic="true">
                        <div class="d-flex">
                            <div class="toast-body">Failed to fetch 2FA code!</div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                        </div>
                    </div>`
                );
                $('.toast').toast({ delay: 5000 });
                $('.toast').toast('show');
            }
        });
    }
    updateCode();
}