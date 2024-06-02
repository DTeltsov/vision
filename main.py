import os

from google.cloud import vision
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from bot_token import TOKEN

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'creds.json'


class ImageAnalyzerBot:
    def __init__(self, token):
        self.client = vision.ImageAnnotatorClient()
        self.mode = None
        self.app = Application.builder().token(token).build()
        self.register_handlers()

    def register_handlers(self):
        self.app.add_handler(CommandHandler("set_mode", self.set_mode))
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

    @staticmethod
    async def start(update: Update, context: CallbackContext) -> None:
        await update.message.reply_text(
            'Привіт! Надішліть мені зображення, і я скажу, що на ньому зображено. '
            'Або оберіть інший режим'
        )
        keyboard = [['/set_mode text', '/set_mode faces', '/set_mode labels']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Please choose a detection mode:', reply_markup=reply_markup)

    async def set_mode(self, update: Update, context: CallbackContext) -> None:
        if context.args:
            self.mode = context.args[0]
            await update.message.reply_text(f"Режим встановлено на {self.mode}. Надішліть зображення.")
        else:
            await update.message.reply_text("Використовуйте /set_mode з одним з параметрів: text, faces, або labels.")

    async def handle_photo(self, update: Update, context: CallbackContext) -> None:
        photo_file = await update.message.photo[-1].get_file()
        photo_file = await photo_file.download_as_bytearray()
        photo_bytes = bytes(photo_file)

        if self.mode == 'text':
            result = self.detect_text(photo_bytes)
        elif self.mode == 'faces':
            result = self.detect_faces(photo_bytes)
        elif self.mode == 'labels':
            result = self.detect_labels(photo_bytes)
        else:
            result = "Спочатку встановіть режим використання команди /set_mode."

        await update.message.reply_text(result)

    def detect_text(self, image_bytes):
        image = vision.Image(content=image_bytes)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        return '\n'.join([text.description for text in texts]) if texts else "Текст не знайдено."

    def detect_faces(self, image_bytes):
        image = vision.Image(content=image_bytes)
        response = self.client.face_detection(image=image)
        faces = response.face_annotations
        return f"Знайдено {len(faces)} облич." if faces else "Облич не знайдено."

    def detect_labels(self, image_bytes):
        image = vision.Image(content=image_bytes)
        response = self.client.label_detection(image=image)
        labels = response.label_annotations
        return ', '.join([label.description for label in labels]) if labels else "Об'єкти не знайдені."

    def run(self):
        self.app.run_polling()


if __name__ == '__main__':
    bot = ImageAnalyzerBot(TOKEN)
    bot.run()
