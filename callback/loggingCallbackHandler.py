import datetime
from langchain_core.callbacks import BaseCallbackHandler
from util.util import logging_history

class LoggingCallbackHandler(BaseCallbackHandler):

    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id = None, tags = None, metadata = None, **kwargs):
        logging_history(f"{'===' * 30}\n")
        logging_history(f"[{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Question :: {inputs["input"]}\n")