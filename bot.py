import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)


TOKEN = os.environ["BOT_TOKEN"]


# مراحل محاسبه
CARD_COUNT, BUY_NOW, REAL_PRICE, QUANTITY, COIN_PRICE = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # پاک کردن کامل اطلاعات محاسبه قبلی
    context.user_data.clear()

    await update.message.reply_text(
        "👋 سلام!\n\n"
        "به ربات محاسبه فاکتور خوش آمدید.\n\n"
        "🔢 چند نوع کارت دارید؟"
    )

    return CARD_COUNT


async def card_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)

        if count <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً یک عدد صحیح معتبر وارد کنید."
        )
        return CARD_COUNT

    context.user_data["total_cards"] = count
    context.user_data["current_card"] = 1
    context.user_data["cards"] = []

    await update.message.reply_text(
        "💰 قیمت Buy Now کارت شماره 1 را وارد کنید:"
    )

    return BUY_NOW


async def buy_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = float(update.message.text)

        if value < 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً یک قیمت معتبر وارد کنید.\n"
            "مثال: 3400"
        )
        return BUY_NOW

    context.user_data["temp_buy_now"] = value

    card = context.user_data["current_card"]

    await update.message.reply_text(
        f"💵 قیمت واقعی کارت شماره {card} را وارد کنید:"
    )

    return REAL_PRICE


async def real_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = float(update.message.text)

        if value < 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً یک قیمت معتبر وارد کنید."
        )
        return REAL_PRICE

    context.user_data["temp_real_price"] = value

    card = context.user_data["current_card"]

    await update.message.reply_text(
        f"🔢 تعداد کارت شماره {card} را وارد کنید:"
    )

    return QUANTITY


async def quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(update.message.text)

        if value <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً تعداد را به صورت عدد صحیح وارد کنید."
        )
        return QUANTITY

    buy_now_price = context.user_data["temp_buy_now"]
    real_price = context.user_data["temp_real_price"]

    context.user_data["cards"].append(
        (buy_now_price, real_price, value)
    )

    current_card = context.user_data["current_card"]
    total_cards = context.user_data["total_cards"]

    if current_card < total_cards:
        next_card = current_card + 1
        context.user_data["current_card"] = next_card

        await update.message.reply_text(
            f"✅ اطلاعات کارت {current_card} ثبت شد.\n\n"
            f"💰 قیمت Buy Now کارت شماره {next_card} را وارد کنید:"
        )

        return BUY_NOW

    await update.message.reply_text(
        "✅ اطلاعات همه کارت‌ها ثبت شد.\n\n"
        "💰 حالا قیمت کوین را وارد کنید:"
    )

    return COIN_PRICE


async def coin_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coin_price_value = float(update.message.text)

        if coin_price_value < 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً قیمت کوین را به صورت عدد وارد کنید."
        )
        return COIN_PRICE

    cards = context.user_data["cards"]

    grand_total = 0
    lines = []

    lines.append("🧾 فاکتور محاسبه")
    lines.append("")

    for i, (buy_now, real_price, qty) in enumerate(cards, start=1):

        formula = buy_now * 0.95 - real_price

        step1 = formula * 1000

        step2 = step1 / 100000

        per_card_money = step2 * coin_price_value

        card_total = per_card_money * qty

        grand_total += card_total

        lines.append(f"کارت {i}")
        lines.append(f"قیمت Buy Now: {buy_now:,.0f}")
        lines.append(f"قیمت واقعی: {real_price:,.0f}")
        lines.append(f"قیمت هر کارت: {per_card_money:,.0f}")
        lines.append(f"تعداد: {qty}")
        lines.append(f"جمع: {card_total:,.0f}")
        lines.append("")

    lines.append(f"💰 جمع کل: {grand_total:,.0f}")

    await update.message.reply_text(
        "\n".join(lines)
    )

    await update.message.reply_text(
        "✅ فاکتور با موفقیت محاسبه شد.\n\n"
        "برای محاسبه فاکتور جدید، /start را بزنید."
    )

    # پاک کردن اطلاعات بعد از پایان محاسبه
    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ محاسبه لغو شد.\n\n"
        "برای شروع دوباره /start را بزنید."
    )

    return ConversationHandler.END


def main():

    app = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(

        entry_points=[
            CommandHandler("start", start)
        ],

        states={

            CARD_COUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    card_count
                )
            ],

            BUY_NOW: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    buy_now
                )
            ],

            REAL_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    real_price
                )
            ],

            QUANTITY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    quantity
                )
            ],

            COIN_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    coin_price
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ],

        # اجازه می‌دهد /start وسط محاسبه هم دوباره اجرا شود
        allow_reentry=True,
    )

    app.add_handler(conversation)

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
