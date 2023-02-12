import requests
import time
import json
import os

class Photo_backup:

    def __init__(self, photos_amount=5):
        # количество выгружаемых фотографий photos_amount по умолчанию 5
        self.photos_amount = photos_amount

    def get_photos(self):
        """
        функция обращается по API ВК и
        возвращает словарь {<количество лайков>:[<URL фотографии>, <размер фото>]}
        """
        # считываем токен из файла
        with open('vk_token.txt', 'r') as file:
            vk_token = file.read().strip()

        self.user_id = input('Введите идентификатор пользователя: ')

        URL = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': self.user_id,
            'album_id': 'profile',
            'access_token': vk_token,
            'extended': 1,
            'v': '5.131'
        }

        # Создаю пустой словарь который будет наполнен лайками и ссылками на фото из ВК
        likes_photos = {}

        # Получаем данные из ВК
        vk_user_data = requests.get(URL, params=params)
        vk_data_dict = vk_user_data.json()
        res_list = vk_data_dict['response']['items']

        # Наполняем словарь нужными данными из res_list
        for elem in res_list:
            like = elem['likes']['count'] + elem['likes']['user_likes']
            if len(likes_photos) < self.photos_amount:
                if like in likes_photos.keys():
                    like_time = str(like) + '_' + time.strftime("%m%d%Y", time.localtime(int(elem['date'])))
                    likes_photos[like_time] = [elem['sizes'][-1]['url'], elem['sizes'][-1]['type']]
                else:
                    likes_photos[like] = [elem['sizes'][-1]['url'], elem['sizes'][-1]['type']]
        return likes_photos

class YaUploader:

    def get_headers(self):

        # Получаем токен для Яндекс.Диск из файла
        with open('ya_token.txt', 'r') as file:
            self.ya_token = file.read().strip()
        return {
            "Content-Type": "application/json",
            "Authorization": "OAuth {}".format(self.ya_token)
        }

    def _get_upload_link(self, disk_file_path):
        """
        Метод возвращает ссылку на Яндекс.Диск
        """
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload?https://sun9-69.userapi.com/c5853/u2612048/-6/w_72e349fe.jpg"
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload(self):
        """Метод загружает файлы по списку file_list на яндекс диск"""

        # Создаем экземпляр класса Photo_backup и получаем словарь от get_photos
        photos = Photo_backup()
        photos_dict = photos.get_photos()

        # создаем переменную для сохранения результата и последующей ее записи в json-файл
        result_list = []

        for key, value in photos_dict.items():

            # Загружаем на ПК фотографию по полученной ссылке из ВК (value)
            img_data = requests.get(value[0]).content
            with open(str(key)+'.jpg', 'wb') as handler:
                handler.write(img_data)

            # Получаем ссылку для загрузки на Я.Диск с названием файла на Я.Диске
            href = self._get_upload_link(disk_file_path="Photo_backup/"+str(key)+".jpg").get("href", "")
            # Загружаем фотографии на Я.Диск
            response = requests.put(href, img_data)

            # Логируем события загрузки фотогрий на Я.Диск
            response.raise_for_status()
            if response.status_code == 201:
                print(f'{key}.jpg Succes')
                result_list.append({"file_name": str(key)+".jpg",
                                    "size": value[-1]})

                # Удаляем jpg файлы из рабочей директории
                dir_name = os.path.abspath(os.curdir)
                photo_files = os.listdir(dir_name)
                for item in photo_files:
                    if item.endswith(".jpg"):
                        os.remove(os.path.join(dir_name, item))
            else:
                print(f'{key}.jpg Error')

        # Записываем в json результат загрузки файлов на Я.Диск
        with open('data.json', 'w') as f:
            json.dump(result_list, f)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    uploader = YaUploader()
    result = uploader.upload()