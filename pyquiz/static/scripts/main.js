$(document).ready(function() {
  $('.choice').on('click', function() {
    checkbox = $(this).children('input');
    checkbox.prop('checked', !checkbox.prop('checked'));
  });
});
