$(function () {

    const isMobile = () => window.innerWidth <= 800;
    const setSidebarState = (state) => localStorage.setItem('sidebarState', state);
    const getSidebarState = () => localStorage.getItem('sidebarState');

    const toggleMainContent = (visible) => {
        $('.main-content')
            .toggleClass('sidebar-visible', visible)
            .toggleClass('sidebar-hidden', !visible);
    };

    const toggleSidebarCollapsedClass = (collapsed) => {
        document.documentElement.classList.toggle('sidebar-collapsed', collapsed);
    };

    const applySidebarState = () => {
        const savedState = getSidebarState();

        if (isMobile()) {
            $('.sidebar').addClass('hidden');
            toggleMainContent(false);
        } else {
            const collapsed = savedState === 'collapsed';
            $('.sidebar').toggleClass('hidden', collapsed);
            toggleMainContent(!collapsed);
            toggleSidebarCollapsedClass(collapsed);
        }
    };

    // Sidebar toggle button
    $('.toggle-btn').on('click', function () {
        const collapsed = $('.sidebar').hasClass('hidden');
        const desktop = !isMobile();

        $('.sidebar').toggleClass('hidden');

        if (desktop) {
            toggleMainContent(collapsed);
            setSidebarState(collapsed ? 'expanded' : 'collapsed');
            toggleSidebarCollapsedClass(!collapsed);
        } else {
            toggleMainContent(collapsed);
            toggleSidebarCollapsedClass(!collapsed);
        }
    });

    // Dropdown click (desktop + mobile)
    $('.manage-link').on('click', function (e) {
        const $parentLi = $(this).closest('.dropdown-manage');
        const $dropdown = $parentLi.find('.manage-dropdown');
        const isOpen = $dropdown.hasClass('expanded');

        if (isMobile()) {
            e.preventDefault();
            $dropdown.toggleClass('expanded');
            $parentLi.toggleClass('open'); // <-- rotate arrow
            $(this).toggleClass('active');
            return;
        }

        e.preventDefault();
        e.stopPropagation();

        // Close all others
        $('.manage-dropdown').removeClass('expanded');
        $('.dropdown-manage').removeClass('open');
        $('.manage-link').removeClass('active');

        // Open current if it was closed
        if (!isOpen) {
            $dropdown.addClass('expanded');
            $parentLi.addClass('open');    // <-- rotate arrow
            $(this).addClass('active');
        }
    });

    // Flyout menus for collapsed sidebar on click
    $('.dropdown-manage > .manage-link').on('click', function (e) {
        const $parent = $(this).closest('.dropdown-manage');

        if ($('.sidebar').hasClass('hidden')) {
            e.preventDefault();
            e.stopPropagation();

            $('.flyout-outside').remove();

            const $flyout = $parent.find('.manage-dropdown').clone().addClass('flyout-outside');
            $('body').append($flyout);

            const offset = $parent.offset();
            $flyout.css({
                top: offset.top,
                left: offset.left + $parent.outerWidth()
            });

            $(document).one('click.flyout', function () {
                $('.flyout-outside').remove();
            });
        }
    });

    // Profile dropdown toggle
    $('#profile-toggle').on('click', function (e) {
        e.stopPropagation();
        $('#profileDropdown').toggleClass('collapsed');
    });

    applySidebarState();
    $(window).on('resize', applySidebarState);
});

$(window).on('load', function () {
    $('.sidebar').removeClass('prepare-transition');
});

// --- Outside click handler with restore default active ---
const $defaultActiveDropdown = $('.manage-dropdown.expanded');
const $defaultActiveLink = $('.manage-link.active');

$(document).on('click', function (e) {
    if (!$(e.target).closest('.dropdown-manage, #profile-toggle, #profileDropdown').length) {

        // Collapse all dropdowns
        $('.manage-dropdown').removeClass('expanded');
        $('.manage-link').removeClass('active open');

        // Restore the default active dropdown & link
        $defaultActiveDropdown.addClass('expanded');
        $defaultActiveLink.addClass('active');

        // Always close profile dropdown
        $('#profileDropdown').addClass('collapsed');
        $('.flyout-outside').remove();
    }
});
