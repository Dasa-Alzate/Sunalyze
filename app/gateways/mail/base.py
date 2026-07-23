

class MailError(Exception):
    pass


class MailGateway:

    def send(self, to, subject, html, locale=None):
        raise NotImplementedError
