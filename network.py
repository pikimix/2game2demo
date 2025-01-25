

import threading
import websocket
import queue
import logging
import json
import uuid
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=0)

class Client:
    def __init__(self, url, port):
        self.url = f"{url}:{port}"
        self.send_queue = queue.Queue()
        self.receive_queue = queue.Queue()
        self.ws = None
        self.thread = None
        self.running = False
    
    def on_message(self, ws, message):
        """Callback function when a message is received."""
        logger.debug('Message received: %s ', message)
        self.receive_queue.put(message)
    
    def on_error(self, ws, error):
        """Callback function when an error occurs."""
        logger.error('WebSocket error: %s', error)
    
    def on_close(self, ws, close_status_code, close_msg):
        """Callback function when the connection is closed."""
        logger.info('WebSocket closed')
    
    def on_open(self, ws):
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
                logger.info('Sending message: %s', message)
                self.ws.send(message)
            except queue.Empty:
                continue
    
    def send(self, message: str):
        """Send message to the server

        Parameters
        ----------
        message : str
            String message to send to the server

        Raises
        ------
        TypeError
            Raised when message is not of type str
        """
        if isinstance(message, str):
            self.send_queue.put(message)
        else:
            raise TypeError(f'Only strings can be sent, not {type(message)}')


    def get_messages(self) -> list:
        """Gets all current received messages in the queue.
            If the queue is empty, returns empty list

        Returns
        -------
        list
            All messages currently in the queue
        """
        if not receive_q.empty():
            ret = []
            while not receive_q.empty():
                ret.append(receive_q.get())
                receive_q.task_done()
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
    client.send(json.dumps({'uuid':str(my_uuid), 'time': time.time()}))

    client.send(json.dumps({'pos':(0,0)}))
    
    # Receiving messages (example)
    try:
        while True:
            msgs = client.get_messages()
            for msg in msgs:
                logger.info('Received Message!')
                logger.info("Received: %s", msg)
    except KeyboardInterrupt:
        client.stop()
