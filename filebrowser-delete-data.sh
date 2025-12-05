docker compose stop filebrowser
sudo rm -rf srv/filebrowser/*
docker compose start filebrowser && docker compose logs filebrowser | grep password
