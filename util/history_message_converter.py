from langchain_community.chat_message_histories.sql import DefaultMessageConverter
from langchain_core.messages import message_to_dict
import json

class HistoryMessageConverter(DefaultMessageConverter):

    def to_sql_model(self, message, session_id: str):
        """db에 등록될 메시지 한글 보존을 위함"""
        return self.model_class(
            session_id=session_id, message=json.dumps(message_to_dict(message), ensure_ascii=False)
        )