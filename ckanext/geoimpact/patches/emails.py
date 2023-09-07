import logging
from ckan.common import _, config
from ckan.lib.base import render
import ckan.lib.helpers as h
from ckan.lib.mailer import mail_recipient, get_reset_link, create_reset_key, mail_user, MailerException

log = logging.getLogger(__name__)


def _send_email(user, subject, template, context):
    """Email the user with the provided subject and context using the given template."""
    if not user.email:
        raise MailerException(_("No recipient email address available!"))

    body = render(template, extra_vars=context)
    mail_recipient(
        recipient_name=user.display_name,
        recipient_email=user.email,
        subject=subject,
        body=body,
        headers={'Content-Type': 'text/html; charset=UTF-8'}
    )


def send_reset_link(user):
    """Send the user a link to reset their password."""
    try:
        reset_link = get_reset_link(user)
        context = {
            'user_name': user.name,
            'reset_link': reset_link,
            'site_title': config.get('ckan.site_title')
        }
        subject = "Password Reset for {}".format(user.name)
        _send_email(user, subject, 'emails/reset_password.html', context)
    except Exception as e:
        log.error(f"Error sending reset link: {e}")
        raise


def send_invite(user, group_dict=None, role=None):
    """Send the user an invitation email."""
    try:
        create_reset_key(user)
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

        subject = f"Invitation to join {config.get('ckan.site_title')}"
        _send_email(user, subject, 'emails/invite_user.html', context)
    except Exception as e:
        log.error(f"Error sending invitation: {e}")
        raise
