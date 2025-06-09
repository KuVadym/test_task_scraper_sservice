# Запуск проекта

## Запуск в Docker

1. Сборка Docker-образа:
    ```bash
    docker build -t listing_project .
    docker run -d --name listing_container -v $(pwd):/listing listing_project
    docker exec -it listing_container python /listing/main_listing.py
    ```

## Без Docker
    ```bash
    python3 -m venv venv t .
    ```
linux:
    
    source venv/bin/activate
wondows:

    venv/Scripts/activate

    pip install --upgrade pip
    pip install -r requirements.txt

# Запуск
    ./venv/bin/python  main_listing.py listiing_example.json 

