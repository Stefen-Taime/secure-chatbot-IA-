<template>
  <div class="chat-bubble" :class="{ 'chat-bubble-user': isUser, 'chat-bubble-assistant': !isUser }">
    <div class="chat-bubble-content">
      <div class="chat-bubble-header">
        <strong>{{ sender }}</strong>
        <span class="chat-bubble-time">{{ formattedTime }}</span>
      </div>
      <div class="chat-bubble-body">{{ content }}</div>
    </div>
  </div>
</template>

<script>
import moment from 'moment';

export default {
  name: 'ChatBubble',
  props: {
    content: {
      type: String,
      required: true
    },
    timestamp: {
      type: String,
      required: true
    },
    isUser: {
      type: Boolean,
      default: false
    },
    sender: {
      type: String,
      default: 'Assistant IA'
    }
  },
  computed: {
    formattedTime() {
      return moment(this.timestamp).format('HH:mm');
    }
  }
};
</script>

<style scoped>
.chat-bubble {
  margin-bottom: 16px;
  display: flex;
}

.chat-bubble-user {
  justify-content: flex-end;
}

.chat-bubble-assistant {
  justify-content: flex-start;
}

.chat-bubble-content {
  max-width: 70%;
  padding: 12px;
  border-radius: 8px;
}

.chat-bubble-user .chat-bubble-content {
  background-color: #e3f2fd;
}

.chat-bubble-assistant .chat-bubble-content {
  background-color: #f5f5f5;
}

.chat-bubble-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 0.85rem;
}

.chat-bubble-time {
  color: rgba(0, 0, 0, 0.6);
}

.chat-bubble-body {
  white-space: pre-line;
}
</style>
