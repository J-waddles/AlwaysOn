# Initialize an empty queue
user_queue = []

# Add a user to the queue
def enqueue_user(user_id):
    if user_id not in user_queue:
        user_queue.append(user_id)

# Remove a user from the queue
def dequeue_user():
    return user_queue.pop(0) if user_queue else None

# Check if the queue has enough users for a pair
def is_pair_available():
    return len(user_queue) >= 2

# Get the next pair from the queue
def get_next_pair():
    if is_pair_available():
        return dequeue_user(), dequeue_user()
    return None, None

# Remove a specific user from the queue
def remove_user_from_queue(user_id):
    if user_id in user_queue:
        user_queue.remove(user_id)
