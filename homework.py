import logging
import os
import sys
import time
from datetime import datetime
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    WrongStatusError, GetStatusException, NotCriticalError
)

logger = logging.getLogger(__name__)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth { PRACTICUM_TOKEN }'}
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/aa'
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности необходимых переменных окружения."""
    tokens_exist = PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID
    if tokens_exist:
        return tokens_exist
    return False


def send_message(bot, message):
    """Отправляет сообщение в telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        message = f'Не удалось отправить сообщение - {error}'
        logger.error(message)
    else:
        logger.debug(f'Бот отправил сообщение: {message}')
    return True


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API."""
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params,
        )
    except requests.exceptions.RequestException as error:
        error_message = f'Ошибка при запросе к API: {error}'
        raise GetStatusException(error_message)
    status_code = homework_statuses.status_code
    if status_code != HTTPStatus.OK:
        raise GetStatusException(
            f'"{ENDPOINT}" - недоступен. Код ответа API: {status_code}'
        )

    return homework_statuses.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Ответ API не является списком')
    return homeworks


def parse_status(homework):
    """
    Функция извлекает статус работы из ответа и возвращает
    строку для отправки пользователю.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not (homework_status and homework_name):
        raise KeyError(
            'В ответе отсутствуют ключи `homework_name` и/или `status`'
        )
    if homework_status not in HOMEWORK_VERDICTS:
        raise WrongStatusError('Получен некорректный статус работы.')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def get_timestamp(report) -> int:
    """
    Функция возвращает время последнего изменения статуса.
    """
    report_update_date = report.get('date_updated')
    report_update_datetime = datetime.strptime(
        report_update_date, '%Y-%m-%dT%H:%M:%SZ'
    )
    report_update_timestamp = int(report_update_datetime.timestamp())
    return report_update_timestamp


def main():
    """Главная функция запуска бота."""
    if not check_tokens():
        logger.critical('Отсутствуют переменные окружения')
        sys.exit('Отсутствуют переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_status = ''
    current_error = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if not len(homework):
                logger.info('Статус не обновлен')
            else:
                homework_status = parse_status(homework[0])
                if current_status == homework_status:
                    logger.info(homework_status)
                else:
                    current_status = homework_status
                    send_message(bot, homework_status)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if current_error != str(error):
                current_error = str(error)
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    main()
