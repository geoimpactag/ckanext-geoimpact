from ckan.lib.base import render
from ckan.lib.mailer import mail_recipient, get_reset_link


def send_reset_link(user):
    """
    Send the user a link to reset their password.
    """
    reset_link = get_reset_link(user)
    context = {
        'user_name': user.name,
        'reset_link': reset_link,
        'site_title': 'Your Site Title'  # Replace with actual site title
    }
    body = render('emails/reset_password.html', extra_vars=context)
    subject = "Password Reset for {}".format(user.name)
    mail_recipient(user.display_name, user.email, subject, body)
