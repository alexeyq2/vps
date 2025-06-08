# есть новый "docker compose" ?
DC="docker compose"
`$DC version > /dev/null 2>&1` || DC="docker-compose"

$DC down
$DC pull
$DC build
$DC up -d
