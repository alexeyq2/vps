#!/bin/bash -e

./down.sh

./update-images.sh
./update-code-and-build.sh

./up.sh

# Функция, которая будет вызвана при нажатии Ctrl+C
cleanup() {
    echo .
    echo "Службы продолжают работать в фоне."
    echo "Для просмотра логов используйте ./log.sh"
    echo "Для остановки всех служб используйте ./down.sh"
    echo "Для запуска служб используйте ./up.sh"
    exit 0
}
# Перехват сигнала SIGINT (Ctrl+C) и вызов функции cleanup
trap cleanup INT

./log.sh
