

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
    def __init__(self, url, port, send_queue, receive_queue):
        self.url = f"{url}:{port}"
        self.send_queue = send_queue
        self.receive_queue = receive_queue
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
        threading.Thread(target=self.send_messages, daemon=True).start()
    
    def send_messages(self):
        """Continuously sends messages from the send queue."""
        while self.running:
            try:
                message = self.send_queue.get(timeout=1)  # Wait for messages
                # message = json.dumps(message)
                logger.info('Sending message: %s', message)
                self.ws.send(message)
            except queue.Empty:
                continue
    
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
    client = Client("ws://127.0.0.1", 8080, send_q, receive_q)
    client.start()
    
    # Sending a test message
    my_uuid = uuid.uuid4()
    send_q.put(json.dumps({'uuid':str(my_uuid), 'time': time.time()}))

    send_q.put(json.dumps({'pos':(0,0)}))
    
    # Receiving messages (example)
    try:
        while True:
            if not receive_q.empty():
                logger.info('Received Message!')
                msg = receive_q.get()
                logger.info("Received: %s", msg)
    except KeyboardInterrupt:
        client.stop()
