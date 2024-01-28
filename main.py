from urllib.parse import urlencode
import requests
from pprint import pprint
from tqdm import tqdm
import json




class VKAPIClient:
    API_BASE_URL = 'https://api.vk.com/method'
    MY_VK_ID = '128573783'

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id

    def get_common_params(self):
        return{
            'access_token': self.token,
            'v': '5.131'
        }

    def are_we_friends(self):
        params = self.get_common_params()
        params.update({'user_ids': self.user_id})
        response = requests.get(f'{self.API_BASE_URL}/friends.areFriends', params=params)
        return response.json().get('response', {})[0]['friend_status']

    def get_profile_photos(self):
        params = self.get_common_params()
        params.update({'owner_id': self.MY_VK_ID, 'album_id': 'profile', 'extended': 1})
        response = requests.get(f'{self.API_BASE_URL}/photos.get', params = params)
        return response.json()


def create_folder_on_yadisk(POLYGON_TOKEN):
    YADISK_BASE_URL = 'https://cloud-api.yandex.net'
    url_create_folder = f'{YADISK_BASE_URL}/v1/disk/resources'
    params = {
        'path': 'VK_Photos'
    }
    headers = {
        'Authorization': f'OAuth {POLYGON_TOKEN}'
    }
    response = requests.put(url_create_folder, params=params, headers=headers)


def upload_to_yadisk(POLYGON_TOKEN, photo_name, photo_url):
    response = requests.get(photo_url)
    with open(f'{photo_name}.jpg', 'wb') as file:
        file.write(response.content)
    YADISK_BASE_URL = 'https://cloud-api.yandex.net'
    url_get_upload = f'{YADISK_BASE_URL}/v1/disk/resources/upload'
    headers = {
        'Authorization': f'OAuth {POLYGON_TOKEN}'
    }
    response = requests.get(url_get_upload,
                            headers = headers,
                            params = {'path': f'VK_Photos/{photo_name}.jpg'})
    url_for_upload = response.json().get('href', '')
    with open(f'{photo_name}.jpg', 'rb') as f:
        response = requests.put(url_for_upload, files={'file': f})


def get_max_size_photo(photo_params_list):
    max_value_of_product_h_w = 0
    index_max_value_photo = 0
    for index, photo in enumerate(photo_params_list):
        product_h_w = photo.get('height','')*photo.get('width','')
        if(product_h_w > max_value_of_product_h_w):
            max_value_of_product_h_w = product_h_w
            index_max_value_photo = index
    height = photo_params_list[index].get('height','')
    width = photo_params_list[index].get('width','')
    url = photo_params_list[index].get('url','')
    return [height, width, url]


def get_photos_names(photos_info_list):
    photos_names = [0]*len(photos_info_list)
    number_of_likes = []
    for photo in photos_info_list:
        number_of_likes.append(photo.get('likes', '').get('count', ''))
    verified_indexes = set()
    for i in range(len(number_of_likes)):
        if i not in verified_indexes:
            photos_names[i] = f'{number_of_likes[i]}'
            flag = 0
            for j in range(len(number_of_likes)):
                if (number_of_likes[i] == number_of_likes[j]
                        and j > i
                        and j not in verified_indexes):
                    flag = 1
                    photos_names[j] = f'{number_of_likes[j]}_{photos_info_list[j].get("date","")}'
                    verified_indexes.add(j)
            if(flag == 1):
                photos_names[i] = f'{number_of_likes[i]}_{photos_info_list[i].get("date","")}'
            verified_indexes.add(i)
    return photos_names


def download_to_json_file(photos_info_for_json):
    with open('photos_info.json', 'w') as f:
        json.dump(photos_info_for_json, f, ensure_ascii=False, indent=2)




if __name__ == '__main__':
    TOKEN_VK = input("Введите токен VK: ")
    POLYGON_TOKEN = input("Введите токен с Полигона Яндекс.Диска: ")
    user_id = input("Введите свой id в vk: ")
    create_folder_on_yadisk(POLYGON_TOKEN)
    vk_client = VKAPIClient(TOKEN_VK, user_id)
    if (vk_client.are_we_friends() != 3):
        print('Мы с вами не друзья!')
    else:
        vk_photos_info = vk_client.get_profile_photos()
        photos_info_list =  vk_photos_info.get('response', {}).get('items', '')
        photos_names = get_photos_names(photos_info_list)
        photos_info_for_json = []
        for index, photo in tqdm(enumerate(photos_info_list), desc = 'Progress'):
            photo_params_list = photo.get('sizes','')
            params_of_max_size_photo = get_max_size_photo(photo_params_list)
            ph_height = params_of_max_size_photo[0]
            ph_width = params_of_max_size_photo[1]
            ph_url = params_of_max_size_photo[2]
            photos_info_for_json.append({'file_name': f'{photos_names[index]}.jpg',
                                         'size': {'height': ph_height,
                                                  'width': ph_width}
                                         })
            upload_to_yadisk(POLYGON_TOKEN, photos_names[index], ph_url)
        download_to_json_file(photos_info_for_json)