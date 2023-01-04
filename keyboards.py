from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton

import config


class MainKeyboards:
    # измененно
    main_but = KeyboardButton('⚠️ Главное меню')
    ad_but = KeyboardButton('🌝 Здесь может быть реклама 🌝')
    rules_but = KeyboardButton('📝 Правила')

    user_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    user_kb.row(main_but, rules_but)
    user_kb.add(ad_but)
    # измененно
    sendall_but = KeyboardButton('📤 Сделать рассылку')
    stats_but = KeyboardButton('📊 Посмотреть статистику')

    admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    admin_kb.row(main_but, rules_but)
    admin_kb.add(ad_but)
    admin_kb.row(sendall_but,stats_but)

    # измененно
    profile_but = InlineKeyboardButton('👨🏻 Профиль', callback_data='profile')
    send_logs_but = InlineKeyboardButton('📤 Отправить логи', callback_data='send_logs')
    sent_logs_but = InlineKeyboardButton('🗂 Отправленные логи', callback_data='history_logs')
    help_but = InlineKeyboardButton('🆘 Поддержка', callback_data='help')

    inline_user_kb = InlineKeyboardMarkup(resize_keyboard=True)
    inline_user_kb.add(profile_but)
    inline_user_kb.add(send_logs_but)
    inline_user_kb.add(sent_logs_but)
    inline_user_kb.add(help_but)


class OtherKeyboards:
    # измененно
    inline_cancel_but = InlineKeyboardButton('↩️️ Отмена', callback_data='cancel')
    inline_cancel_kb = InlineKeyboardMarkup(resize_keyboard=True)
    inline_cancel_kb.add(inline_cancel_but)

    inline_close_but = InlineKeyboardButton('❌ Закрыть', callback_data='close')
    inline_close_kb = InlineKeyboardMarkup(resize_keyboard=True)
    inline_close_kb.add(inline_close_but)

    inline_back_but = InlineKeyboardButton('↩️ Назад', callback_data='back')
    inline_back_kb = InlineKeyboardMarkup(resize_keyboard=True)
    inline_back_kb.add(inline_back_but)

    back_but = KeyboardButton('↩️ Назад', callback_data='back')
    back_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    back_kb.add(back_but)

    inline_checklog_kb = InlineKeyboardMarkup(resize_keyboard=True)
    inline_addbalance_but = InlineKeyboardButton('💰 Есть бабосики', callback_data='add_balance')
    inline_break_but = InlineKeyboardButton('❌ Пусто', callback_data='break_logs')
    inline_delMarkup_but = InlineKeyboardButton('🗑 Удалить кнопки', callback_data='delete_buttons')
    inline_checklog_kb.row(inline_addbalance_but,inline_break_but)
    inline_checklog_kb.row(inline_delMarkup_but)


    inline_profile = InlineKeyboardMarkup(resize_keyboard=True)
    inline_profile.add(InlineKeyboardButton('💵 Вывести бабло', callback_data='withdraw_button'))
    inline_profile.add(inline_back_but)

async def generateHistory(history):
    history = sorted(history, reverse=True)
    kb = InlineKeyboardMarkup(resize_keyboard=True)
    if len(history) > 0:
        if len(history) < 10:
            k = len(history)
        else:
            k = 10
        for i in range(0,k):
            j = history[i]
            if j[-1] == 0:
                kk = '❌'
            else:
                kk = '✅'
            kb.add(InlineKeyboardButton(f"№{j[0]} | {j[2]} руб. | {j[3].split()[0]} | {kk}", callback_data='hui'))
    else:
        # измененно
        kb.add(InlineKeyboardButton(f"Нет отправленных логов", callback_data='hui'))

    kb.add(OtherKeyboards.inline_back_but)
    return kb

async def generateFilterKeyboard(kb):
    if type(kb) == type(dict()):
        inline_next_but = InlineKeyboardButton('Продолжить ➡️', callback_data='next')

        inline_filter_keyboard = InlineKeyboardMarkup(row_width=2)
        srv = kb
        temp = list(srv)



        for i in range(0,len(srv),2):
            try:
                next = temp[i + 1]
            except (ValueError, IndexError):
                next = None

            if srv[temp[i]] == 1:
                i1 = InlineKeyboardButton("✅ " + temp[i], callback_data="service:" + temp[i].replace(' ', '_'))
            else:
                i1 = InlineKeyboardButton("❌ " + temp[i], callback_data="service:" + temp[i].replace(' ', '_'))

            try:
                if srv[next] == 1:
                    i2 = InlineKeyboardButton("✅ " + next, callback_data="service:" + next.replace(' ', '_'))
                else:
                    i2 = InlineKeyboardButton("❌ " + next, callback_data="service:" + next.replace(' ', '_'))

                inline_filter_keyboard.row(i1, i2)
            except:
                inline_filter_keyboard.add(i1)

        inline_filter_keyboard.row(OtherKeyboards.inline_back_but, inline_next_but)

        return inline_filter_keyboard

    else:
        inline_next_but = InlineKeyboardButton('Продолжить ➡️', callback_data='next')

        inline_filter_keyboard = InlineKeyboardMarkup(row_width=2)
        srv = kb
        for i in range(0, len(srv), 2):
            try:
                inline_filter_keyboard.row(InlineKeyboardButton("❌ "+srv[i], callback_data="service:"+srv[i].replace(' ', '_')),InlineKeyboardButton("❌ "+srv[i+1], callback_data="service_"+srv[i+1].replace(' ', '_')))
            except:
                inline_filter_keyboard.add(InlineKeyboardButton("❌ "+srv[i], callback_data="service:"+srv[i].replace(' ', '_')))
        inline_filter_keyboard.row(OtherKeyboards.inline_back_but, inline_next_but)

        return inline_filter_keyboard

