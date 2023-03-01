class GetStatusException(Exception):
    """Ошибка при получении статуса домашнего задания."""
    pass


class HomeworkServiceError(Exception):
    """.
    Базовый класс исключений для ошибок, возникающих при взаимодействии с
    сервисом Практикум.Домашка.
    """
    pass


class WrongStatusError(HomeworkServiceError):
    """
    Исключение возникает в случае, если в ответе получен не предусмотренный
    словарем `UPDATE_MESSAGES` статус работы.
    """
    pass


class NotCriticalError(Exception):
    pass
