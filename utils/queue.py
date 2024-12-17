queues = {}  # Server-specific queues

def enqueue_user(server_id, user_id):
    if server_id not in queues:
        queues[server_id] = []
    if user_id not in queues[server_id]:
        queues[server_id].append(user_id)

def dequeue_user(server_id):
    return queues[server_id].pop(0) if queues.get(server_id) and queues[server_id] else None

def is_pair_available(server_id):
    return len(queues.get(server_id, [])) >= 2

def get_next_pair(server_id):
    if is_pair_available(server_id):
        return dequeue_user(server_id), dequeue_user(server_id)
    return None, None

def remove_user_from_queue(server_id, user_id):
    if server_id in queues and user_id in queues[server_id]:
        queues[server_id].remove(user_id)
