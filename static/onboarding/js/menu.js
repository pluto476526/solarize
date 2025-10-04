jQuery(document).ready(function ($) {
    var MQL = 1170;

    // header show/hide on scroll
    if ($(window).width() > MQL) {
        var headerHeight = $('.box-header').height();
        $(window).on('scroll',
            { previousTop: 0 },
            function () {
                var currentTop = $(window).scrollTop();

                // scrolling up
                if (currentTop < this.previousTop) {
                    if (currentTop > 0 && $('.box-header').hasClass('is-fixed')) {
                        $('.box-header').addClass('is-visible');
                    } else {
                        $('.box-header').removeClass('is-visible is-fixed');
                    }
                } else {
                    // scrolling down
                    $('.box-header').removeClass('is-visible');
                    if (currentTop > headerHeight && !$('.box-header').hasClass('is-fixed')) {
                        $('.box-header').addClass('is-fixed');
                    }
                }
                this.previousTop = currentTop;
            });
    }

    // open/close primary navigation
    $('.box-primary-nav-trigger').on('click', function () {
        $('.box-menu-icon').toggleClass('is-clicked');
        $('.box-header').toggleClass('menu-is-open');

        if ($('.box-primary-nav').hasClass('is-visible')) {
            $('.box-primary-nav').removeClass('is-visible').one('transitionend webkitTransitionEnd oTransitionEnd MSTransitionEnd', function () {
                $('body').removeClass('overflow-hidden');
            });
        } else {
            $('.box-primary-nav').addClass('is-visible').one('transitionend webkitTransitionEnd oTransitionEnd MSTransitionEnd', function () {
                $('body').addClass('overflow-hidden');
            });
        }
    });

    // close menu + smooth scroll when clicking nav links
    $('.box-primary-nav li a').on('click', function (e) {
        var target = $(this).attr('href');

        // if it's an anchor link on the same page
        if (target.startsWith('#') && target.length > 1) {
            e.preventDefault();

            // smooth scroll
            $('html, body').animate({
                scrollTop: $(target).offset().top - 50 // offset for header
            }, 600);
        }

        // close menu
        $('.box-menu-icon').removeClass('is-clicked');
        $('.box-header').removeClass('menu-is-open');
        $('.box-primary-nav').removeClass('is-visible');
        $('body').removeClass('overflow-hidden');
    });
});
