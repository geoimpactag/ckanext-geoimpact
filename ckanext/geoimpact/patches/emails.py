from ckan.common import _, config
from ckan.lib.base import render
import ckan.lib.helpers as h
from ckan.lib.mailer import mail_recipient, get_reset_link, create_reset_key, mail_user, MailerException


def send_reset_link(user):
    """
    Send the user a link to reset their password.
    """
    if (user.email is None) or not len(user.email):
        raise MailerException(_("No recipient email address available!"))
    
    reset_link = get_reset_link(user)
    context = {
        'user_name': user.name,
        'reset_link': reset_link,
        'site_title': config.get('ckan.site_title')
    }
    body = render('emails/reset_password.html', extra_vars=context)
    subject = "Password Reset for {}".format(user.name)
    mail_recipient(
        recipient_name=user.display_name,
        recipient_email=user.email,
        subject=subject,
        body=body,
        headers={'Content-Type': 'text/html; charset=UTF-8'}
    )


def send_invite(user, group_dict=None, role=None):
    if (user.email is None) or not len(user.email):
        raise MailerException(_("No recipient email address available!"))

    create_reset_key(user)

    # Construct the reset link
    reset_link = get_reset_link(user)

    context = {
        'reset_link': reset_link,
        'site_title': config.get('ckan.site_title'),
        'site_url': config.get('ckan.site_url'),
        'user_name': user.name,
    }

    if role:
        context['role_name'] = h.roles_translated().get(role, _(role))
    if group_dict:
        group_type = (_('organization') if group_dict['is_organization']
                      else _('group'))
        context['group_type'] = group_type
        context['group_title'] = group_dict.get('title')

    body = render('emails/invite_user.html', extra_vars=context)
    subject = "Invitation to join {}".format(config.get('ckan.site_title'))

    # Ensure only the first line is used as the subject
    subject = subject.split('\n')[0]

    mail_recipient(
        recipient_name=user.display_name,
        recipient_email=user.email,
        subject=subject,
        body=body,
        headers={'Content-Type': 'text/html; charset=UTF-8'}
    )
