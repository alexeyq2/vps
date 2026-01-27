docker compose stop filebrowser
sudo rm -rf srv/filebrowser/*
docker compose start filebrowser && sleep 3 && docker compose logs filebrowser | grep password
