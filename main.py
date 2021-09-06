# coding=utf8
import requests
import random
import telebot
from telebot import types
from telebot.types import InlineKeyboardButton
import re
import pymongo
import cherrypy
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import cherrypy_cors
from cherrypy.lib.httputil import parse_query_string
import sys

API_KEY = "YOUR API KEY"
bot = telebot.TeleBot(API_KEY)
client = pymongo.MongoClient(host="localhost", port=27017)
db = client["sudoku"]
games_coll = db.get_collection("games")
users_coll = db.get_collection("users")
pays_coll = db.get_collection("pays")
moves_coll = db.get_collection("moves")

prices = {
    "40": 5000,
    "100": 11000,
    "200": 19000,
    "500": 38000,
    "1000": 69000
}

WEBHOOK_HOST = 'localhost'
WEBHOOK_PORT = 20000  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_URL_PATH = "/%s/" % (API_KEY)
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
# bot.remove_webhook()

SAMPLE = [[1, 5, 2, 6, 3, 4],
          [4, 3, 6, 1, 2, 5],
          [2, 4, 5, 3, 1, 6],
          [6, 1, 3, 5, 4, 2],
          [3, 6, 4, 2, 5, 1],
          [5, 2, 1, 4, 6, 3]]

GUIDE = '☑️ راهنمای بازی محبوب سودوکو🔢\n\n✌️ یک بازی جدول اعداد معروف به مینی سودوکو یا سودوکوی کوچک که 6 سطر و 6 ستون دارد\n\nروش بازی: در این بازی می بایست اعداد 1 و 2 و 3 و 4 و 5 و 6  را مطابق شکل به گونه ای در جدول قرار دهید که هیچ عدد تکراری در ستون، سطر و همچنین مستطیل های مشخص شده نداشته باشیم\n\n🔲🔲🔲⬜️⬜️⬜️\n🔲🔲🔲⬜️⬜️⬜️\n⬜️⬜️⬜️🔲🔲🔲\n⬜️⬜️⬜️🔲🔲🔲\n🔲🔲🔲⬜️⬜️⬜️\n🔲🔲🔲⬜️⬜️⬜️\n\n\nانواع بازی: این بازی را هم به صورت تک نفره داخل ربات و هم به صورت چند نفره(دوستان) در گروهها، کانال یا پیوی میتوانید انجام دهید.\nبازی دوستانه در سه حالت ساده، متوسط و سخت در دسترس است.\nجهت انجام بازی دوستانه کافیست از طریق منو و دکمه    بازی با دوستان اقدام نمایید یا از طریق تایپ آدرس ربات در مکانی که قصد بازی دارید\n\nامتیاز : هر عدد درست 3 امتیاز مثبت  و عدد غلط 2 امتیاز منفی\nلازم به ذکر است که امتیاز بازیهای انفرادی داخل ربات، تاثیری در رتبه و ارتقا سطح ندارد.\n\nراهنما و آیتم: \nآیتم جارو که یک خانه را انتخاب کرده و عدد صحیح آن خانه توسط ربات به نفع شما گذاشته می شود\nآیتم جهش که عدد صحیح یک خانه به انتخاب خود ربات به نفع شما قرار داده می شود.\nلازم به ذکر است که در هر بازی فقط یک بار مجاز به استفاده از آیتم و آن هم به شرط داشتن سکه هستید.\n\n🤖 @MiniSudokuBot\n📣 @TRexGames'
LEVELS = [50, 105, 165, 231, 304, 384, 472, 569, 676, 793, 922, 1064, 1220, 1392, 1581, 1789, 2018, 2270, 2547, 2852,
          3188, 3558, 3965, 4412, 4904, 5445, 6040, 6695, 7416, 8209, 9081, 10040, 11095, 12256, 13533, 14938, 16483,
          18183, 20053, 22110, 24372, 26861, 29599, 32611, 35924, 39568, 43576, 47985, 52835, 58170, 64039, 70495,
          77597, 85409, 94002, 103454, 113852, 125290, 137871, 151711, 166935, 183681, 202102, 222365, 244654, 269172,
          296142, 325809, 358443, 394340, 433827, 477263, 525042, 577599, 635412, 699006, 768960, 845909, 930553,
          1023662, 1126082, 1238744, 1362672, 1498993, 1648946, 1813894, 1995337, 2194924, 2414470, 2655971, 2921622,
          3213838, 3535275, 3888856, 4277795, 4705628, 5176245, 5693923, 6263369, 6889760]


# bot.set_webhook(url="https://sudoku.appteams.ir/api/v1.1/telegram-web-hook")


def check_column(sudoku, tmp, j):
    isInColumn = False
    for k in range(0, len(sudoku)):
        if tmp == sudoku[k][j]:
            isInColumn = True
    return isInColumn


def print_sudoku(sudoku):
    for row in sudoku:
        for number in row:
            print(number, end=" ")
        print()
    print("========")


def check_surroundings(sudoku, i, j, tmp):
    if i == 0 or i == 2 or i == 4:
        return False
    else:
        if (j == 0 or j == 3) and (tmp == sudoku[i - 1][j + 1] or tmp == sudoku[i - 1][j + 2]):
            return True
        elif (j == 1 or j == 4) and (tmp == sudoku[i - 1][j - 1] or tmp == sudoku[i - 1][j + 1]):
            return True
        elif (j == 2 or j == 5) and (tmp == sudoku[i - 1][j - 1] or tmp == sudoku[i - 1][j - 2]):
            return True
        else:
            return False
    return False


def check_surroundings2(sudoku, i, j, tmp):
    elements = []
    tmp_i = (i // 2) * 2
    tmp_j = (j // 3) * 3
    for m in range(0, 2):
        tmp_i += m
        for n in range(0, 3):
            if i == tmp_i and tmp_j == j:
                continue
            elements.append(sudoku[tmp_i][tmp_j + n])
    if tmp in elements:
        return True
    return False


def init_random_arr(arr):
    for i in random.randint(0, 35):
        if i not in arr:
            arr.append(i)


def arr_copy(src, dst):
    for i, row in enumerate(src):
        dst.append([])
        for element in row:
            dst[i].append(element)


def solve_sudoku(sudoku, i, j, counter):
    if i == -1 and j == -1:
        return counter
    for k in range(0, 6):
        if check_column(sudoku, k + 1, j) or check_surroundings2(sudoku, i, j, k + 1) or ((k + 1) in sudoku[i]):
            continue
        else:
            sudoku[i][j] = k + 1
            sudoku_copy = []
            arr_copy(sudoku, sudoku_copy)
            indices = get_zero_index(sudoku_copy)
            if indices == [-1, -1]:
                counter += 1
            else:
                counter = solve_sudoku(sudoku_copy, indices[0], indices[1], counter)
    return counter


def randomize(sudoku, type):
    indices = [x for x in range(36)]
    counter = 0
    if type == 'e':
        counter = 8
    if type == 'm':
        counter = 5
    tmp_sudoku = []
    arr_copy(sudoku, tmp_sudoku)
    random.shuffle(indices)
    for x in indices:
        i = x // 6
        j = x % 6
        tmp = sudoku[i][j]
        sudoku[i][j] = 0
        zero_indices = get_zero_index(sudoku)
        sudoku_copy = []
        arr_copy(sudoku, sudoku_copy)
        if solve_sudoku(sudoku_copy, zero_indices[0], zero_indices[1], 0) > 1:
            sudoku[i][j] = tmp
    if type == 'h':
        return sudoku
    random.shuffle(indices)
    while counter != 0:
        x = indices.pop()
        i = x // 6
        j = x % 6
        if sudoku[i][j] != 0:
            counter += 1
        sudoku[i][j] = tmp_sudoku[i][j]
        counter -= 1
    return sudoku


def get_zero_index(sudoku):
    for i, row in enumerate(sudoku):
        for j, element in enumerate(row):
            if element == 0:
                return [i, j]
    return [-1, -1]


def get_total_rank(users, id):
    previous_rank = 0
    previous_point = 0
    for i, user in enumerate(users):
        if i == 0:
            previous_rank = 1
            previous_point = user["total_point"]
        elif previous_point != user["total_point"]:
            previous_point = user["total_point"]
            previous_rank += 1
        if str(user["_id"]) == str(id):
            return previous_rank
    return ''


def return_character(number):
    if number == 0:
        return "0️⃣"
    elif number == 1:
        return "1️⃣"
    elif number == 2:
        return "2️⃣"
    elif number == 3:
        return "3️⃣"
    elif number == 4:
        return "4️⃣"
    elif number == 5:
        return "5️⃣"
    elif number == 6:
        return "6️⃣"
    elif number == 7:
        return "7️⃣"
    elif number == 8:
        return "8️⃣"
    elif number == 9:
        return "9️⃣"


def create_keyboards(sudoku, game_id):
    keyboards = []
    for i, row in enumerate(sudoku):
        keyboards_row = []
        for j, number in enumerate(row):
            if number != 0:
                if (i == 2 or i == 3) and j < 3:
                    keyboards_row.append(
                        InlineKeyboardButton(number, callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
                elif (i == 0 or i == 1) and j >= 3:
                    keyboards_row.append(
                        InlineKeyboardButton(number, callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
                elif (i == 4 or i == 5) and j >= 3:
                    keyboards_row.append(
                        InlineKeyboardButton(number, callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
                else:
                    keyboards_row.append(
                        InlineKeyboardButton(return_character(number),
                                             callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
            else:
                if (i == 2 or i == 3) and j < 3:
                    keyboards_row.append(
                        InlineKeyboardButton("⬜️", callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
                elif (i == 0 or i == 1) and j >= 3:
                    keyboards_row.append(
                        InlineKeyboardButton("⬜️", callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
                elif (i == 4 or i == 5) and j >= 3:
                    keyboards_row.append(
                        InlineKeyboardButton("⬜️", callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
                else:
                    keyboards_row.append(
                        InlineKeyboardButton("🔲", callback_data="s" + str(i) + "" + str(j) + "/" + game_id))
        keyboards.append(keyboards_row)

    empty = []
    empty.append(InlineKeyboardButton("️️", callback_data="empty"))
    keyboards.append(empty)
    numbers = []
    for i in range(0, 6):
        numbers.append(InlineKeyboardButton(return_character(i + 1), callback_data="n" + str(i + 1) + "/" + game_id))
    keyboards.append(numbers)
    items = []
    items.append(InlineKeyboardButton('جارو🧹', callback_data='broom/' + game_id))
    items.append(InlineKeyboardButton('جهش💥', callback_data='jump/' + game_id))
    keyboards.append(items)
    keyboards.append([InlineKeyboardButton(' 🤝 بازی با دوستانم(گروه، کانال و ...) 🤝', switch_inline_query="")])
    return types.InlineKeyboardMarkup(keyboards)


def create_finish_keyboards(sudoku, mode):
    keyboards = []
    for i, row in enumerate(sudoku):
        keyboards_row = []
        for j, number in enumerate(row):
            if (i == 2 or i == 3) and j < 3:
                keyboards_row.append(
                    InlineKeyboardButton(number, url="t.me/MiniSudokuBot"))
            elif (i == 0 or i == 1) and j >= 3:
                keyboards_row.append(
                    InlineKeyboardButton(number, url="t.me/MiniSudokuBot"))
            elif (i == 4 or i == 5) and j >= 3:
                keyboards_row.append(
                    InlineKeyboardButton(number, url="t.me/MiniSudokuBot"))
            else:
                keyboards_row.append(
                    InlineKeyboardButton(return_character(number), url="t.me/MiniSudokuBot"))
        keyboards.append(keyboards_row)
    if mode == 'single':
        again = InlineKeyboardButton('🔁 دوباره', callback_data="again single")
    else:
        again = InlineKeyboardButton('🔁 دوباره', switch_inline_query_current_chat="")
    keyboards.append([InlineKeyboardButton('🛒 فروشگاه', callback_data='shop'),
                      again])
    keyboards.append([InlineKeyboardButton(' 🤝 بازی با دوستانم(گروه، کانال و ...) 🤝', switch_inline_query="")])
    keyboards.append([InlineKeyboardButton('🎮🟡 بازیهای تیرکس 🟡🎮', url='https://t.me/TRexGames/599')])
    return types.InlineKeyboardMarkup(keyboards)


def create_sudoku(game_id, type):
    while True:
        sudoku = []
        reset = False
        for i in range(0, 6):
            row = []
            numbers = [1, 2, 3, 4, 5, 6]
            for j in range(0, 6):
                tmp = numbers[random.randint(0, len(numbers) - 1)]
                tmp_numbers = numbers[:]
                while tmp in row or check_column(sudoku, tmp, j) or check_surroundings(
                        sudoku, i, j, tmp):
                    tmp_numbers.remove(tmp)
                    if (len(tmp_numbers) == 0): break
                    tmp = tmp_numbers[random.randint(0, len(tmp_numbers) - 1)]
                if len(tmp_numbers) == 0:
                    reset = True
                    break
                row.append(tmp)
                numbers.remove(tmp)
            if reset:
                break
            sudoku.append(row)
        if reset:
            continue
        print_sudoku(sudoku)
        games_coll.update_one({"_id": game_id}, {"$set": {"sudoku": sudoku}})
        randomize(sudoku, type)
        print_sudoku(sudoku)
        sudoku_copy = []
        arr_copy(sudoku, sudoku_copy)
        games_coll.update_one({"_id": game_id}, {"$set": {"randomized_sudoku": sudoku}})
        return create_keyboards(sudoku, str(game_id))


def single_player_sudoku(message, game_id):
    bot.send_message(message.from_user.id,
                     "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 بازی انفرادی\n\n🔰امتیازات\n" + create_text(
                         games_coll.find_one({"_id": ObjectId(game_id)})["users"], str(game_id)) + '\n🤖@MiniSudokuBot',
                     reply_markup=create_sudoku(game_id, 'e'))


def create_text(users, game_id):
    text = ''
    points = {}
    for i in users:
        moves = moves_coll.find_one({"user_id": i["user_id"], "game_id": ObjectId(game_id)})["moves"]
        if len(moves) == 0:
            points[i["user_id"]] = 0
        else:
            point = 0
            for x in moves:
                point += x["point"]
            points[i["user_id"]] = point
    points = dict(sorted(points.items(), key=lambda x: x[1], reverse=True))
    previous_point = next(iter(points.values()))
    previous_rank = 1
    for i, id in enumerate(points):
        line = u'\u200e'
        user = users_coll.find_one({"_id": int(id)})
        if i == 0:
            line = return_character(1)
        elif i != 0 and points[id] == previous_point:
            for x in str(previous_rank):
                line += return_character(int(x))
        else:
            previous_point = points[id]
            previous_rank += 1
            for x in str(previous_rank):
                line += return_character(int(x))
        line += user["first_name"] + '  🎖' + str(user["total_rank"]) + '\n' + "🔰" + str(points[id]) + '  〽️' + str(
            user["level"]) + "\n\n"
        text = line + text
        if i >= 25:
            text = "و " + str(len(points) - 25) + " نفر دیگر ...\n" + text
            break
    return text


def games_count(user_id):
    count = games_coll.count_documents({"users.user_id": str(user_id)})
    return str(count)


def get_past_seven_rank(games, user_id):
    points = {}
    for game in games:
        for user in game["users"]:
            if user["user_id"] not in points:
                points[user["user_id"]] = user["point"]
            else:
                points[user["user_id"]] += user["point"]
    points = dict(sorted(points.items(), key=lambda x: x[1], reverse=True))
    if user_id not in list(points.keys()):
        return ''
    return str(list(points.keys()).index(user_id) + 1)


def get_element(id, arr, index_str):
    return next((item for item in arr if item[index_str] == id), None)


def get_past_seven_points(games, user_id):
    point = 0
    for game in games:
        point += get_element(user_id, game['users'], "user_id")["point"]
    return str(point)


def update_profiles(users, game_id):
    for i in users:
        total_points = users_coll.find_one({"_id": int(i["user_id"])})["total_point"]
        moves = moves_coll.find_one({"user_id": i["user_id"], "game_id": ObjectId(game_id)})["moves"]
        points = 0
        for point in moves:
            points += point["point"]
        games_coll.update_one({"_id": ObjectId(game_id), "users.user_id": i["user_id"]}, {"$set": {
            "users.$.point": points
        }})
        total_points += points
        users_coll.update_one({"_id": int(i["user_id"])}, {"$set": {"total_point": total_points}})
        for j, level in enumerate(LEVELS):
            if total_points < level:
                if users_coll.find_one({"_id": int(i["user_id"])})["level"] < j:
                    try:
                        bot.send_message(chat_id=int(i["user_id"]),
                                         text="💪ایول " + users_coll.find_one({"_id": int(i["user_id"])})[
                                             "first_name"] + "\nتبریک!🎊  سطح شما به " + str(
                                             j) + " ارتقا یافت و 10 سکه هدیه گرفتی\n🕺🕺💃💃")

                    except Exception as e:
                        print(e)
                    users_coll.update_one({"_id": int(i["user_id"])},
                                          {"$set": {"total_point": total_points, "level": j},
                                           "$inc": {"coins": 10}})
                break
    for i in users:
        users_coll.update_one({"_id": int(i["user_id"])}, {
            "$set": {"total_rank": get_total_rank(users_coll.find({}).sort("total_point", -1), i["user_id"])}})


def get_total_ranking(users):
    text = 'رنکینگ امتیاز کل\n\n'
    counter = 1
    for i, user in enumerate(users):
        # print(user)
        if user["total_rank"] == '':
            counter -= 1
            continue
        text += u'\u200e' + str(counter) + ". " + user["first_name"] + '  ' + str(user["total_point"]) + '\n'
        counter += 1
        if counter == 51:
            break
    text += '\n🤖 @MiniSudokuBot\n📣 @TRexGames'
    return text


def get_seven_ranking(games):
    points = {}
    for game in games:
        for user in game["users"]:
            try:
                if user["user_id"] not in points:
                    points[user["user_id"]] = user["point"]
                else:
                    points[user["user_id"]] += user["point"]
            except Exception as e:
                pass
    points = dict(sorted(points.items(), key=lambda x: x[1], reverse=True))
    text = 'رنکینگ هفت روز اخیر\n\n'
    counter = 0
    for i, user in enumerate(points):
        user_prof = users_coll.find_one({"_id": int(user)})
        if user_prof is not None:
            text += u'\u200e' + str(i + 1) + ". " + user_prof["first_name"] + '   ' + str(points[user]) + "\n"
            counter += 1
        if counter == 50:
            break
    text += '\n🤖 @MiniSudokuBot\n📣 @TRexGames'
    return text


def insert_game(message, type, mode):
    game_id = games_coll.insert_one(
        {"mode": mode, "type": type, "is_complete": False, "date": datetime.today().replace(microsecond=0),
         "users": [{"user_id": str(message.from_user.id), "jump": False,
                    "broom": False, "use_broom": False}]}).inserted_id
    moves_coll.insert_one({"game_id": game_id, "user_id": str(message.from_user.id), "moves": []})
    return game_id


@bot.message_handler(commands=['update'])
def update(message):
    if message.from_user.id != 396539934:
        return
    bot.send_message(message.from_user.id, "started!")
    games_coll.update_many({"$expr": {
        "$eq": ["$sudoku", "$randomized_sudoku"]
    }
    }, {
        "$set": {
            "is_complete": True
        }
    })
    games = games_coll.find(
        {"is_complete": True, "date": {"$gte": datetime.today().replace(microsecond=0) - timedelta(7)}})
    for game in games:
        for user_stat in game["users"]:
            try:
                moves = moves_coll.find_one({"game_id": game["_id"], "user_id": user_stat["user_id"]})["moves"]
                point = 0
                for i in moves:
                    point += i["point"]
                games_coll.update_one({"_id": game["_id"], "users.user_id": user_stat["user_id"]}, {"$set": {
                    "users.$.point": point
                }})
            except Exception as e:
                print(e)
                pass
    bot.send_message(message.from_user.id, "done!")


@bot.message_handler(commands=['start'])
def start(message):
    print("start", message)
    if '/start shop' == message.text:
        text = '🛒 فروشگاه\n\n📚هر راهنمای جارو  یا جهش  5 سکه نیاز دارد\n\n👇برای خرید سکه یکی از موارد زیر را ' \
               'انتخاب نمایید👇 '
        markup = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('💰 40 سکه💰 👈 5000 تومان', callback_data='c40'),
            types.InlineKeyboardButton('💰 100 سکه💰 👈 11000 تومان', callback_data='c100'),
            types.InlineKeyboardButton('💰 200 سکه💰 👈 19000 تومان', callback_data='c200'),
            types.InlineKeyboardButton('💰 500 سکه💰 👈 38000 تومان', callback_data='c500'),
            types.InlineKeyboardButton('💰 1000 سکه💰 👈 69000 تومان', callback_data='c1000')
        )
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=markup)
        return
    try:
        if len(message.from_user.first_name) > 20:
            message.from_user.first_name = message.from_user.first_name[0:20]
        users_coll.insert_one(
            {"_id": message.from_user.id, "first_name": message.from_user.first_name, "total_point": 0,
             "coins": 20,
             "level": 0, "total_rank": ''})
    except Exception as e:
        print(e)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    single_player_btn = types.KeyboardButton("🏆 بازی تک نفره")
    multi_player_btn = types.KeyboardButton("🤝 بازی چند نفره")
    profile_btn = types.KeyboardButton("👤 پروفایل")
    champions_btn = types.KeyboardButton("🏅 قهرمانان")
    shop_btn = types.KeyboardButton("🛒 فروشگاه")
    guide_btn = types.KeyboardButton("📚 راهنما")
    markup.add(single_player_btn, multi_player_btn, profile_btn, champions_btn, shop_btn, guide_btn)
    bot.send_message(message.chat.id, "به بازی سودوکو خوش آمدید", reply_markup=markup)


@bot.message_handler()
def menu(message):
    print("message", message)
    try:
        if len(message.from_user.first_name) > 20:
            message.from_user.first_name = message.from_user.first_name[0:20]
        users_coll.insert_one(
            {"_id": message.from_user.id, "first_name": message.from_user.first_name, "total_point": 0,
             "coins": 20,
             "level": 0, "total_rank": ''})
    except Exception as e:
        print(e)
    if message.text == "🏆 بازی تک نفره":
        if bot.get_chat_member(-1001319848880, message.from_user.id).status == 'left':
            markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("عضویت در کانال", url="https://t.me/TRexGames"))
            bot.send_message(message.chat.id,
                             "کاربر " + message.from_user.first_name + "\nبرای ساخت بازی ابتدا عضو کانال زیر شوید 👇\n@TRexGames",
                             reply_markup=markup)
            return
        game_id = insert_game(message, "easy", "single")
        single_player_sudoku(message, game_id)
    elif message.text == "🤝 بازی چند نفره":
        if bot.get_chat_member(-1001319848880, message.from_user.id).status == 'left':
            markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("عضویت در کانال", url="https://t.me/TRexGames"))
            bot.send_message(message.chat.id,
                             "کاربر " + message.from_user.first_name + "\nبرای ساخت بازی ابتدا عضو کانال زیر شوید 👇\n@TRexGames",
                             reply_markup=markup)
            return
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("یک گروه انتخاب کن", switch_inline_query=""))
        bot.send_message(message.chat.id, "برای بازی چند نفره بر روی دکمه ی زیر کلیک کنید : ", reply_markup=markup)
    elif message.text == "👤 پروفایل":
        user = users_coll.find_one({"_id": message.from_user.id})
        text = 'پروفایل\n\n' + '👤نام   👈 ' + user["first_name"] + '\n💎سطح  👈 ' + str(
            user["level"]) + '\n🔰 تعداد بازی  👈 ' + str(games_coll.count_documents(
            {"users.user_id": str(message.from_user.id)})) + '\n〽️ امتیاز تا سطح بعد  👈 ' + str(
            LEVELS[user["level"]] - user["total_point"]) + '\n🎖 رتبه 👈 ' + str(user["level"]) + '\n💰سکه 👈 ' + str(
            user["coins"]) + '\n\nاسپانسر @TRexGames'
        bot.send_message(chat_id=message.chat.id, text=text)
    elif message.text == "📚 راهنما":
        bot.send_message(chat_id=message.chat.id, text=GUIDE)
    elif message.text == "🏅 قهرمانان":
        user = users_coll.find_one({"_id": message.from_user.id})
        total_rank = user["total_rank"]

        past_seven_days_points = get_past_seven_points(
            games_coll.find({"date": {"$gte": datetime.today().replace(microsecond=0) - timedelta(7)}, "mode": "multi",
                             "users.user_id": str(message.from_user.id), "is_complete": True}, {"users": 1}),
            str(message.from_user.id))
        past_seven_days_rank = get_past_seven_rank(games_coll.find(
            {"date": {"$gte": datetime.today().replace(microsecond=0) - timedelta(7)}, "mode": "multi",
             "is_complete": True},
            {"users": 1}),
            str(message.from_user.id))

        markup = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton('رنکینگ هفت روز اخیر', callback_data="seven ranking"),
            types.InlineKeyboardButton('رنکینگ کل', callback_data="total ranking"))
        bot.send_message(chat_id=message.chat.id,
                         text='قهرمانان\n\n' + '👤نام   👈 ' + message.from_user.first_name + '\n\nامتیاز کل  👈 ' +
                              str(user["total_point"]) + "\n🔰رتبه کل  👈 " + str(
                             total_rank) + "\n\nامتیاز هفت روز اخیر " + past_seven_days_points + "\n🔰 رتبه هفت روز اخیر 👈 " + past_seven_days_rank + "\n\nاسپانسر @TRexGames",
                         reply_markup=markup)

    elif message.text == "🛒 فروشگاه":
        text = '🛒 فروشگاه\n\n📚هر راهنمای جارو  یا جهش  5 سکه نیاز دارد\n\n👇برای خرید سکه یکی از موارد زیر را ' \
               'انتخاب نمایید👇 '
        markup = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('💰 40 سکه💰 👈 5000 تومان', callback_data='c40'),
            types.InlineKeyboardButton('💰 100 سکه💰 👈 11000 تومان', callback_data='c100'),
            types.InlineKeyboardButton('💰 200 سکه💰 👈 19000 تومان', callback_data='c200'),
            types.InlineKeyboardButton('💰 500 سکه💰 👈 38000 تومان', callback_data='c500'),
            types.InlineKeyboardButton('💰 1000 سکه💰 👈 69000 تومان', callback_data='c1000')
        )

        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=markup)


@bot.chosen_inline_handler(func=lambda message: True)
def handler(message):
    print("chosen", message)
    if bot.get_chat_member(-1001319848880, message.from_user.id).status == 'left':
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("عضویت در کانال", url="https://t.me/TRexGames"))
        bot.edit_message_text(
            text="کاربر " + message.from_user.first_name + "\nبرای ساخت بازی ابتدا عضو کانال زیر شوید 👇\n@TRexGames",
            inline_message_id=message.inline_message_id,
            reply_markup=markup)
        return
    if message.result_id == '6x6h':
        game_id = insert_game(message, "hard", "multi")
        text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 سطح سخت\n\n🔰امتیازات\n" + create_text(
            games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
        bot.edit_message_text(text=text, inline_message_id=message.inline_message_id,
                              reply_markup=create_sudoku(game_id, 'h'))
    elif message.result_id == '6x6e':
        game_id = insert_game(message, "easy", "multi")
        text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 سطح آسان\n\n🔰امتیازات\n" + create_text(
            games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
        bot.edit_message_text(text=text, inline_message_id=message.inline_message_id,
                              reply_markup=create_sudoku(game_id, 'e'))
    elif message.result_id == '6x6m':
        game_id = insert_game(message, "medium", "multi")
        text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 سطح متوسط\n\n🔰امتیازات\n" + create_text(
            games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
        bot.edit_message_text(text=text, inline_message_id=message.inline_message_id,
                              reply_markup=create_sudoku(game_id, 'm'))


@bot.inline_handler(func=lambda query: True)
def inline_handler(message):
    print("inline", message)
    try:
        if len(message.from_user.first_name) > 20:
            message.from_user.first_name = message.from_user.first_name[0:20]
        users_coll.insert_one(
            {"_id": message.from_user.id, "first_name": message.from_user.first_name, "total_point": 0,
             "coins": 20,
             "level": 0, "total_rank": ''})

    except Exception as e:
        print(e)
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("⏳", callback_data="1"))
    text = "در حال ساخت..."
    h = types.InlineQueryResultArticle(id='6x6h', title='🔴 سودوکو سطح سخت',
                                       input_message_content=types.InputTextMessageContent(text),
                                       thumb_url="https://appteams.ir/sudoku/hard.png"
                                       , reply_markup=markup)
    e = types.InlineQueryResultArticle(id='6x6e', title='🟣 سودوکو سطح ساده',
                                       input_message_content=types.InputTextMessageContent(text),
                                       thumb_url="https://appteams.ir/sudoku/easy.png"
                                       , reply_markup=markup)
    m = types.InlineQueryResultArticle(id='6x6m', title='🟠 سودوکو سطح متوسط',
                                       input_message_content=types.InputTextMessageContent(text),
                                       thumb_url="https://appteams.ir/sudoku/medium.png"
                                       , reply_markup=markup)
    bot.answer_inline_query(message.id, [e, m, h])


@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    print("call", call)
    try:
        if len(call.from_user.first_name) > 20:
            call.from_user.first_name = call.from_user.first_name[0:20]
        users_coll.insert_one(
            {"_id": call.from_user.id, "first_name": call.from_user.first_name, "total_point": 0,
             "coins": 20,
             "level": 0, "total_rank": ''})

    except Exception as e:
        print(e)
    if 'total ranking' == call.data:
        markup = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton('رنکینگ هفت روز اخیر', callback_data="seven ranking"),
            types.InlineKeyboardButton('رنکینگ کل', callback_data="total ranking"))

        text = get_total_ranking(users_coll.find({}).sort("total_point", -1))

        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text,
                              reply_markup=markup)
    elif call.data == 'again single':
        game_id = insert_game(call, "easy", "single")
        single_player_sudoku(call, game_id)
    elif call.data == 'shop':
        bot.answer_callback_query(url='t.me/MiniSudokuBot?start=shop', callback_query_id=call.id)
    elif call.data == 'seven ranking':
        markup = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton('رنکینگ هفت روز اخیر', callback_data="seven ranking"),
            types.InlineKeyboardButton('رنکینگ کل', callback_data="total ranking"))

        text = get_seven_ranking(games_coll.find(
            {"date": {"$gte": datetime.today().replace(microsecond=0) - timedelta(7)}, "mode": "multi"},
            {"users": 1}))

        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text,
                              reply_markup=markup)
    elif call.data == 'c40' or call.data == 'c100' or call.data == 'c200' or call.data == 'c500' or call.data == 'c1000':
        coins = int(re.sub('c', '', call.data))
        client_id = pays_coll.insert_one({"user_id": call.from_user.id, "coins": coins, "status": "paying",
                                          "date": datetime.today().replace(microsecond=0)}).inserted_id
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 8a65d585ce24ea37cc87359866f186fcb3ec3782e6b18ac59317188bb5725ab7"
        }
        params = {
            "amount": str(prices[str(coins)]),
            "payerIdentity": "",
            "payerName": "",
            "description": "",
            "returnUrl": "https://appteams.ir/verify-200.html",
            "clientRefId": str(client_id)
        }
        r = requests.post(url="https://api.payping.ir/v1/pay", json=params, headers=headers).json()
        try:
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('تکمیل پرداخت',
                                                                                 url="https://appteams.ir/verify-200.html?code=" +
                                                                                     r["code"] + ""))
            bot.edit_message_text('برای تکمیل خرید خود بر روی دکمه ی زیر کلیک کنید:', call.from_user.id,
                                  call.message.id, reply_markup=markup)



        except Exception as e:
            print(e)

    elif 'jump' in call.data or 'broom' in call.data:
        split = call.data.split("/")
        game_id = ObjectId(split[1])
        data = split[0]
        user_id = str(call.from_user.id)
        user = users_coll.find_one({"_id": int(user_id)})
        game = games_coll.find_one({"_id": game_id})
        randomized_sudoku = game["randomized_sudoku"]
        sudoku = game["sudoku"]
        if len(game["users"]) == 1 and get_element(user_id, game["users"], "user_id") is not None:
            bot.answer_callback_query(call.id, "اول دیگر بازیکنان باید شروع کنند!")
            return
        if get_element(user_id, game["users"], "user_id") is None:
            games_coll.update_one({"_id": game_id}, {
                "$push": {"users": {"user_id": user_id, "jump": False,
                                    "broom": False, "use_broom": False}}})
            moves_coll.insert_one({"game_id": game_id, "user_id": user_id, "moves": []})
            game = games_coll.find_one({"_id": game_id})
        game_user = get_element(user_id, game["users"], "user_id")
        if (game_user["jump"] and data == 'jump') or (
                game_user["broom"] and data == 'broom' and not game_user[
            "use_broom"]):
            bot.answer_callback_query(text='شما قبلا از این آیتم استفاده کرده اید.', callback_query_id=call.id)
            return
        if user["coins"] < 5:
            bot.answer_callback_query(call.id, 'شما سکه ی کافی برای استفاده از این آیتم را ندارید.')
            return
        if data == 'jump':
            zero_indices = []
            for i, row in enumerate(randomized_sudoku):
                for j, element in enumerate(row):
                    if element == 0:
                        zero_indices.append(i * 6 + j)
            index = zero_indices[random.randint(0, len(zero_indices) - 1)]
            i = index // 6
            j = index % 6
            call.data = 'n' + str(sudoku[i][j]) + "/" + str(game_id)
            moves = moves_coll.find_one({"game_id": game_id, "user_id": user_id})["moves"]
            length = len(moves)
            games_coll.update_one({"_id": game_id, "users.user_id": str(call.from_user.id)},
                                  {"$set": {"users.$.jump": True}})
            if len(moves) == 0 or moves[- 1]["n"] != 0:
                moves_coll.update_one({"game_id": game_id, "user_id": str(call.from_user.id)},
                                      {"$push": {"moves": {"i": i,
                                                           "j": j,
                                                           "n": 0,
                                                           "point": 0
                                                           }}})
            else:
                moves_coll.update_one({"game_id": game_id, "user_id": str(call.from_user.id)},
                                      {"$set": {"moves." + str(length - 1): {
                                          "i": i,
                                          "j": j,
                                          "n": 0,
                                          "point": 0
                                      }}})
            users_coll.update_one({"_id": call.from_user.id}, {"$inc": {"coins": -5}})
        elif data == 'broom':
            games_coll.update_one({"_id": game_id, "users.user_id": str(call.from_user.id)},
                                  {"$set": {"users.$.broom": True,
                                            "users.$.use_broom": True}})
            bot.answer_callback_query(call.id, 'حالا یک خونه رو انتخاب کن!')

    if re.search(r's[0-5][0-5]', call.data) or re.search(r'n[1-6]', call.data):
        game_id = str(call.data).split("/")[1]
        game_id = ObjectId(game_id)
        user_id = str(call.from_user.id)
        doc = games_coll.find_one({"_id": game_id})
        length = 0
        randomized_sudoku = doc["randomized_sudoku"]
        # print_sudoku(randomized_sudoku)
        if doc["mode"] == "multi":
            if get_element(user_id, doc["users"], "user_id") is None:
                games_coll.update_one({"_id": game_id}, {
                    "$push": {"users": {"user_id": user_id, "jump": False,
                                        "broom": False, "use_broom": False}}})
                moves_coll.insert_one({"game_id": game_id, "user_id": user_id, "moves": []})
                hardness = doc["type"]
                if hardness == 'easy':
                    hardness = 'آسان'
                elif hardness == 'medium':
                    hardness = 'متوسط'
                else:
                    hardness = 'سخت'
                text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 سطح " + hardness + "\n\n🔰امتیازات\n" + create_text(
                    games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
                bot.edit_message_text(text=text, inline_message_id=call.inline_message_id,
                                      reply_markup=create_keyboards(randomized_sudoku, str(game_id)))
                doc = games_coll.find_one({"_id": game_id})
            if len(doc["users"]) == 1:
                bot.answer_callback_query(call.id, "اول دیگر بازیکنان باید شروع کنند!")
                return
        moves = moves_coll.find_one({"game_id": game_id, "user_id": str(call.from_user.id)})["moves"]
        length = len(moves)
        sudoku = doc["sudoku"]
        if re.search(r's[0-5][0-5]', call.data):
            soduku_id = str(call.data).split("/")[0]
            indices = [int(i) for i in re.sub(r's', '', soduku_id)]
            if randomized_sudoku[indices[0]][indices[1]] != 0:
                bot.answer_callback_query(call.id, "این خانه خالی نیست!")
                return
            else:
                if length == 0:
                    moves_coll.update_one({"game_id": game_id, "user_id": str(call.from_user.id)}, {"$push": {"moves": {
                        "i": indices[0],
                        "j": indices[1],
                        "n": 0,
                        "point": 0
                    }}})
                elif moves[-1]["n"] == 0:
                    moves_coll.update_one({"game_id": game_id, "user_id": str(call.from_user.id)}, {"$set": {
                        "moves." + str(length - 1): {
                            "i": indices[0],
                            "j": indices[1],
                            "n": 0,
                            "point": 0
                        }
                    }})
                else:
                    moves_coll.update_one({"game_id": game_id, "user_id": str(call.from_user.id)}, {"$push": {
                        "moves": {
                            "i": indices[0],
                            "j": indices[1],
                            "n": 0,
                            "point": 0
                        }
                    }})
                game_user = get_element(user_id, doc["users"], "user_id")
                if game_user["broom"] and game_user["use_broom"]:
                    call.data = 'n' + str(sudoku[indices[0]][indices[1]]) + '/' + str(soduku_id)
                    games_coll.update_one({"_id": game_id, "users.user_id": str(call.from_user.id)},
                                          {"$set": {"users.$.use_broom": False}})
                    users_coll.update_one({"_id": call.from_user.id}, {"$inc": {"coins": -5}})
                else:
                    bot.answer_callback_query(call.id, "حالا عدد مورد نظرت رو انتخاب کن")
        if re.search(r'n[1-6]', call.data):
            moves = moves_coll.find_one({"game_id": game_id, "user_id": str(call.from_user.id)})["moves"]
            length = len(moves)
            if length == 0:
                bot.answer_callback_query(call.id, "شما هنوز خانه ای انتخاب نکردید!")
                return
            elif moves[- 1]["n"] != 0:
                bot.answer_callback_query(call.id, "شما هنوز خانه ای انتخاب نکردید!")
            elif moves[- 1]["n"] == 0:
                numbers_id = str(call.data).split("/")[0]
                number = re.sub(r'n', '', numbers_id)
                number = int(number)
                i = moves[- 1]["i"]
                j = moves[- 1]["j"]
                if randomized_sudoku[i][j] != 0:
                    bot.answer_callback_query(call.id, 'این خانه خالی نیست!')
                elif randomized_sudoku[i][j] == 0 and sudoku[i][j] == number:
                    randomized_sudoku[i][j] = number
                    games_coll.update_one({"_id": game_id}, {"$set": {"randomized_sudoku": randomized_sudoku}})
                    point = 0
                    if length != 0:
                        for k in moves:
                            point += k["point"]
                    moves_coll.update_one({"game_id": game_id, "user_id": str(call.from_user.id)},
                                          {"$set": {"moves." + str(length - 1): {
                                              "i": i,
                                              "j": j,
                                              "n": number,
                                              "point": 3
                                          }}})
                    if randomized_sudoku == sudoku:
                        games_coll.update_one({"_id": game_id},
                                              {"$set": {"is_complete": True}})
                        if doc["mode"] == 'single':
                            text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 بازی انفرادی" + "\n\n🇮🇷پایان بازی🇮🇷\n" + create_text(
                                games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
                            bot.edit_message_text(text,
                                                  call.from_user.id,
                                                  call.message.message_id,
                                                  reply_markup=create_finish_keyboards(sudoku, 'single'))

                        else:
                            hardness = games_coll.find_one({"_id": game_id})["type"]
                            if hardness == 'easy':
                                hardness = 'آسان'
                            elif hardness == 'medium':
                                hardness = 'متوسط'
                            else:
                                hardness = 'سخت'
                            points = {}
                            game = games_coll.find_one({"_id": game_id})
                            for i in game["users"]:
                                moves = moves_coll.find_one({"game_id": game_id, "user_id": i["user_id"]})["moves"]
                                username = users_coll.find_one({"_id": int(i["user_id"])})["first_name"]
                                if len(moves) == 0:
                                    points[username] = 0
                                else:
                                    point = 0
                                    for x in moves:
                                        point += x["point"]
                                    points[username] = point
                            points = dict(sorted(points.items(), key=lambda x: x[1], reverse=True))
                            text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 سطح " + hardness + "\n\n🇮🇷پایان بازی🇮🇷\n" + create_text(
                                games_coll.find_one({"_id": game_id})["users"],
                                str(game_id)) + '\n🏆 این بازی با برتری ' + \
                                   list(points.keys())[0] + ' به پایان رسید👏🕺💃\n🤖@MiniSudokuBot'
                            update_profiles(games_coll.find_one({"_id": game_id})["users"], game_id)
                            bot.edit_message_text(text=text, inline_message_id=call.inline_message_id,
                                                  reply_markup=create_finish_keyboards(sudoku, 'multi'))
                    else:
                        if doc["mode"] == 'single':
                            text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 بازی انفرادی" + "\n\n🔰امتیازات\n" + create_text(
                                games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
                            bot.edit_message_text(text=
                                                  text,
                                                  chat_id=call.from_user.id,
                                                  message_id=call.message.message_id,
                                                  reply_markup=create_keyboards(randomized_sudoku, str(game_id)))
                        else:
                            hardness = doc["type"]
                            if hardness == 'easy':
                                hardness = 'آسان'
                            elif hardness == 'medium':
                                hardness = 'متوسط'
                            else:
                                hardness = 'سخت'
                            text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 سطح " + hardness + "\n\n🔰امتیازات\n" + create_text(
                                games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
                            bot.edit_message_text(text=text, inline_message_id=call.inline_message_id,
                                                  reply_markup=create_keyboards(randomized_sudoku, str(game_id)))
                        bot.answer_callback_query(call.id, "آفرین!👍")

                else:
                    point = 0
                    if length != 0:
                        for k in moves:
                            point += k["point"]
                    moves_coll.update_one({"game_id": game_id, "user_id": str(call.from_user.id)},
                                          {"$set": {"moves." + str(length - 1): {
                                              "i": i,
                                              "j": j,
                                              "n": number,
                                              "point": -2
                                          }}})
                    if doc["mode"] == 'single':
                        text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 بازی انفرادی" + "\n\n🔰امتیازات\n" + create_text(
                            games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
                        bot.edit_message_text(text=
                                              text,
                                              chat_id=call.from_user.id,
                                              message_id=call.message.message_id,
                                              reply_markup=create_keyboards(randomized_sudoku, str(game_id)))
                    else:
                        hardness = doc["type"]
                        if hardness == 'easy':
                            hardness = 'آسان'
                        elif hardness == 'medium':
                            hardness = 'متوسط'
                        else:
                            hardness = 'سخت'
                        text = "🔢 مینی سودوکو 🔢\n\n📚قراردادن اعداد 1 تا 6 در جدول بدون تکرار در سطر، ستون و مستطیل مشخص شده\n💎 سطح " + hardness + "\n\n🔰امتیازات\n" + create_text(
                            games_coll.find_one({"_id": game_id})["users"], str(game_id)) + '\n🤖@MiniSudokuBot'
                        bot.edit_message_text(text=text, inline_message_id=call.inline_message_id,
                                              reply_markup=create_keyboards(randomized_sudoku, str(game_id)))
                    bot.answer_callback_query(call.id, "واای😢")


while True:
    bot.polling()


