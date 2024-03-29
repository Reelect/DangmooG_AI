import os
import json

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from application.nvshopping import get_search_url, get_result_page, get_mean_price_nv
from application.joongna import scrap_joogna_price


openai_api_key = os.environ.get('OPEN_AI_API_KEY')  # openai api key
client_id = os.environ.get('NAVER_ID')
client_secret = os.environ.get('NAVER_SECRET')


def set_config(config_path):
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)

    db_config = config_data.get('ndev_config', {})

    client_id = db_config.get('client_id', '')
    client_secret = db_config.get('client_secret', '')

    return client_id, client_secret


def get_rec_price(upper, lower, alpha) -> int:
    recommend_price = (1 - alpha) * upper + alpha * lower
    return int(round(recommend_price, -1))


def get_results_list(upper, recommend, lower) -> list:
    results = set([round(upper, -1), round(recommend, -1), round(lower, -1)])
    results = sorted(list(results), reverse=True)
    results = list(map(int, list(results)))
    return results


app = FastAPI(title="Dangmuzi-AI", debug=True)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/predict/get_price",
    name="가격 추천 획득 beta version",
    description="글의 제목을 title에 넣어주기만 하면 됩니다."
                "\n\n"
                "결과는 가격의 리스트 형태로 반환됩니다."
)
async def predict_api(title: str) -> list:
    alpha = 0.5

    url = get_search_url(title, 1, 5)
    result = get_result_page(url, client_id, client_secret)
    new_mean_price = get_mean_price_nv(result)  # 새상품 기준 평균가

    trend_price, lower_price = scrap_joogna_price(title)
    if trend_price != 0:
        if new_mean_price >= trend_price:
            upper_price = get_rec_price(new_mean_price, trend_price, alpha)
        else:
            upper_price = new_mean_price * 0.9

    else:
        upper_price = get_rec_price(new_mean_price, new_mean_price * 0.6, alpha)
        lower_price = new_mean_price * 0.6

    recommend_price = get_rec_price(upper_price, lower_price, alpha)
    results = get_results_list(upper_price, recommend_price, lower_price)

    return results
