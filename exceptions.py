class GetStatusException(Exception):
    """Ошибка при получении статуса домашнего задания."""
    pass


class HomeworkServiceError(Exception):
    """.
    Класс исключений для ошибок.
    """
    pass


class WrongStatusError(HomeworkServiceError):
    """
    Исключение возникает в случае, если в ответе получен не предусмотренный
    словарем статус работы.
    """
    pass


class GetAPIAnswerException(Exception):
    pass