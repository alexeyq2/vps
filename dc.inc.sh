yamls=(compose*.yaml)
FILES=${yamls[@]}
OPT=""
for y in $FILES; do
  OPT="$OPT -f $y"
done
#
export DC="docker compose $OPT"
echo -e "\033[0;34m  [$DC] \033[0;34m"
