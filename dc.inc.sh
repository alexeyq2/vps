# есть новый "docker compose" ?
export DC="docker compose"
`$DC version > /dev/null 2>&1` || export DC="docker-compose"

# echo DC=$DC
