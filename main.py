import requests
import time
import json
import os
import configparser

class VK_get_data:
    """
    Класс предназначен для работы с API VK
    """
    # считываем токен из файла
    config = configparser.ConfigParser()  # создаём объекта парсера
    config.read("/Users/denistimakov/PycharmProjects/TestingYaUpload/settings.ini")  # читаем конфиг
    config['DEFAULT']['vk_token']
    vk_token = config['DEFAULT']['vk_token']

    def search_user(self):
        """
        Метод поиска пользователя ВК по названию страницы либо по идентификатору
        Возвращает идентификатор пользователя
        """
        choise = input(
            'Для поиска по названию страницы введите 1, для поиска по идентификатору введите 2: ')

        if choise == '1':

            URL = 'https://api.vk.com/method/utils.resolveScreenName'
            screen_name = input('Введите название страницы: ')

            params = {
                'screen_name': screen_name,
                'access_token': self.vk_token,
                'extended': 1,
                'v': '5.131'
            }

            res = requests.get(URL, params=params)
            res_dict = res.json()
            user_id = res_dict['response']['object_id']

        elif choise == '2':
            user_id = input('Введите идентификатор пользователя: ')

        else:
            print('Введена не корректная команда')

        return user_id

    def vk_get_data(self):
        """
        Метод обращается по API VK и возвращает данные о пользователе
        """
        URL = 'https://api.vk.com/method/photos.get'
        user_id = self.search_user()
        params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'access_token': self.vk_token,
            'extended': 1,
            'v': '5.131'
        }

        # Получаем данные из ВК
        vk_user_data = requests.get(URL, params=params)
        vk_data_dict = vk_user_data.json()

        return vk_data_dict

class Photo_backup:

    def __init__(self, photos_amount=5):
        # количество выгружаемых фотографий photos_amount по умолчанию 5
        self.photos_amount = photos_amount

    def get_photos(self):
        """
        Метод возвращает словарь {<количество лайков>:[<URL фотографии>, <размер фото>]}
        """

        # Создаю пустой словарь который будет наполнен лайками и ссылками на фото из ВК
        likes_photos = {}

        # Получаем данные из ВК
        get_vk_data = VK_get_data()
        get_data = get_vk_data.vk_get_data()
        res_list = get_data['response']['items']
        self.photos_amount = int(input("Введите количество фотографий для сохранения: "))

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
    """
    Класс предназначен для работы с API Yandex.Диск
    """

    def get_headers(self):

        # Получаем токен для Яндекс.Диск из файла
        config = configparser.ConfigParser()  # создаём объекта парсера
        config.read("/Users/denistimakov/PycharmProjects/TestingYaUpload/settings.ini")  # читаем конфиг
        config['DEFAULT']['vk_token']
        self.ya_token = config['DEFAULT']['ya_token']

        return {
            "Content-Type": "application/json",
            "Authorization": "OAuth {}".format(self.ya_token)
        }

    def check_folder(self):
        """
        Метод для проверки наличия папки Photo_backup на Яндекс.Диск
        Возвращает информацию о директории в виде словаря
        """
        check_url = "https://cloud-api.yandex.net/v1/disk/resources?path=disk%3A%2FPhoto_backup"
        headers = self.get_headers()
        response = requests.get(check_url, headers=headers)
        folder_info = response.json()
        return folder_info

    def create_folder(self):
        """
        Метод для создания директории в Я.Диск для бэкапа
        возвращает информацию о созданной или существующей директории
        """
        current_folder = self.check_folder()
        if 'DiskNotFoundError' in current_folder.values():
            create_url = "https://cloud-api.yandex.net/v1/disk/resources"
            headers = self.get_headers()
            params = {"path": "Photo_backup"}
            response = requests.put(create_url, headers=headers, params=params)
            return response.json()
        else:
            return current_folder

    def _get_upload_link(self, disk_file_path):
        """
        Метод возвращает ссылку на Яндекс.Диск
        """
        create_dir = self.create_folder()
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload?https://sun9-69.userapi.com/c5853/u2612048/-6/w_72e349fe.jpg"
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

class Photo_upload:

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
            get_link = YaUploader()
            href = get_link._get_upload_link(disk_file_path="Photo_backup/"+str(key)+".jpg").get("href", "")
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
        return result_list

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    uploader = Photo_upload()
    result = uploader.upload()

    def save_result():
        # Записываем в json результат загрузки файлов на Я.Диск
        with open('data.json', 'w') as f:
            json.dump(result, f)