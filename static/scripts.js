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

let refreshInterval = null;

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
                    stop2FARefresh();
                    return;
                }
                $('#current-code').text(data.code).addClass('animate__animated animate__pulse');
                $('#remaining-time').text(data.remaining);
                $('#progress-bar').css('width', (data.remaining / 30 * 100) + '%');
                setTimeout(() => $('#current-code').removeClass('animate__animated animate__pulse'), 500);
                refreshInterval = setTimeout(updateCode, 1000);
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
                stop2FARefresh();
            }
        });
    }
    updateCode();

    // Add event listener for the Stop button
    $('#stop-refresh').on('click', function () {
        stop2FARefresh();
        $('.toast-container').append(
            `<div class="toast animate__slideInRight align-items-center text-white bg-info border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">2FA code refresh stopped!</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>`
        );
        $('.toast').toast({ delay: 5000 });
        $('.toast').toast('show');
        $('#code-display').hide(); // Optionally hide the code display
    });
}

function stop2FARefresh() {
    if (refreshInterval) {
        clearTimeout(refreshInterval);
        refreshInterval = null;
    }
}
