"""Module used for connecting to a remote websocket server
"""

import json
import logging
import threading
import time
import queue
import uuid
import websocket

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class Client:
    """Class that creates a websocket Client to send and receive messages to a websocket server
    """
    def __init__(self, url: str, port):
        """Creates a websocket Client

        Parameters
        ----------
        url : str
            URL to connect to
        port : int
            Port the remote server is listening on
        """
        self.url = f"{url}:{port}"
        self.send_queue = queue.Queue()
        self.receive_queue = queue.Queue()
        self.ws = None
        self.thread = None
        self.running = False

    def on_message(self, ws, message): # pylint: disable=unused-argument
        """Callback function when a message is received."""
        logger.debug('Message received: %s ', message)
        self.receive_queue.put(json.loads(message))

    def on_error(self, ws, error): # pylint: disable=unused-argument
        """Callback function when an error occurs."""
        logger.error('WebSocket error: %s', error)

    def on_close(self, ws, close_status_code, close_msg): # pylint: disable=unused-argument
        """Callback function when the connection is closed."""
        logger.info('WebSocket closed')

    def on_open(self, ws): # pylint: disable=unused-argument
        """Callback function when the connection is opened."""
        logger.info("WebSocket connection opened")
        self.running = True
        threading.Thread(target=self._send_messages, daemon=True).start()

    def _send_messages(self):
        """Continuously sends messages from the send queue."""
        while self.running:
            try:
                message = self.send_queue.get(timeout=1)  # Wait for messages
                # message = json.dumps(message)
                logger.debug('Sending message: %s', message)
                self.ws.send(json.dumps(message))
            except queue.Empty:
                continue

    def send(self, message: dict):
        """Send message to the server

        Parameters
        ----------
        message : dict
            Dictionary message to send to the server

        Raises
        ------
        TypeError
            Raised when message is not of type dict
        """
        if isinstance(message, dict):
            self.send_queue.put(message)
        else:
            raise TypeError(f'Only dicts can be sent, not {type(message)}')


    def get_messages(self) -> list:
        """Gets all current received messages in the queue.
            If the queue is empty, returns empty list

        Returns
        -------
        list
            All messages currently in the queue
        """
        if not self.receive_queue.empty():
            ret = []
            while not self.receive_queue.empty():
                ret.append(self.receive_queue.get())
                self.receive_queue.task_done()
            return ret
        else:
            return []

    def start(self):
        """Starts the WebSocket connection in a separate thread."""
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the WebSocket connection."""
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join()

# Example usage
if __name__ == "__main__":
    send_q = queue.Queue()
    receive_q = queue.Queue()
    client = Client("ws://127.0.0.1", 8080)
    client.start()

    # Sending a test message
    my_uuid = uuid.uuid4()
    client.send({'uuid':str(my_uuid), 'time': (time.time() * 1000)})

    client.send({'pos':(0,0)})

    # Receiving messages (example)
    try:
        while True:
            msgs = client.get_messages()
            for msg in msgs:
                logger.info('Received Message!')
                logger.info("Received: %s", msg)
    except KeyboardInterrupt:
        client.stop()
